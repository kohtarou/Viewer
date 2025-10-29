import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pydicom
import numpy as np
from PIL import Image, ImageTk
import os

class DicomViewerApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("DICOM 3断面ビューア")
        self.root.geometry("1000x700")

        self.volume = None
        self.tk_images = {}
        self.debounce_job = None
        self.is_loading = False # ロード中のリサイズイベントを無視するフラグ

        # --- 【修正点】メインレイアウトを PanedWindow (左右分割) に変更 ---
        self.pw_main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.pw_main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- 左側：画像表示パネル ---
        image_panel = ttk.Frame(self.pw_main)
        self.pw_main.add(image_panel, weight=3) # 左側を全体の 3/4 の幅に

        # --- 【修正点】画像パネル内を PanedWindow (上下分割) に変更 ---
        self.pw_images = ttk.PanedWindow(image_panel, orient=tk.VERTICAL)
        self.pw_images.pack(fill=tk.BOTH, expand=True)

        # 1. 上：Axial (Canvas)
        axial_frame = ttk.LabelFrame(self.pw_images, text="Axial (上から)")
        self.pw_images.add(axial_frame, weight=1) # 上半分
        axial_frame.rowconfigure(0, weight=1)
        axial_frame.columnconfigure(0, weight=1)
        self.axial_canvas = tk.Canvas(axial_frame, bg="black", highlightthickness=0)
        self.axial_canvas.grid(row=0, column=0, sticky="nsew")

        # 2. 下：Sagittal/Coronal (Notebook)
        self.notebook = ttk.Notebook(self.pw_images)
        self.pw_images.add(self.notebook, weight=1) # 下半分
        
        # Sagittalタブ
        sagittal_frame = ttk.Frame(self.notebook, padding=0)
        self.notebook.add(sagittal_frame, text="Sagittal (横から)")
        sagittal_frame.rowconfigure(0, weight=1)
        sagittal_frame.columnconfigure(0, weight=1)
        self.sagittal_label = ttk.Label(sagittal_frame, background="black", anchor="center")
        self.sagittal_label.grid(row=0, column=0, sticky="nsew")

        # Coronalタブ
        coronal_frame = ttk.Frame(self.notebook, padding=0)
        self.notebook.add(coronal_frame, text="Coronal (正面から)")
        coronal_frame.rowconfigure(0, weight=1)
        coronal_frame.columnconfigure(0, weight=1)
        self.coronal_label = ttk.Label(coronal_frame, background="black", anchor="center")
        self.coronal_label.grid(row=0, column=0, sticky="nsew")


        # --- 右側：コントロールパネル ---
        control_panel = ttk.Frame(self.pw_main)
        self.pw_main.add(control_panel, weight=1) # 右側を全体の 1/4 の幅に
        
        # 1. 読み込みボタン
        load_frame = ttk.Frame(control_panel)
        load_frame.pack(side=tk.TOP, fill=tk.X, pady=5, padx=5)
        self.load_button = ttk.Button(load_frame, text="DICOMフォルダ読込", command=self.load_dicom_folder)
        self.load_button.pack(fill=tk.X)

    # メニューバーは表示しない（シンプルな UI を維持）

        # 2. ステータスラベル
        self.status_label = ttk.Label(control_panel, text="フォルダを読み込んでください", wraplength=230)
        self.status_label.pack(side=tk.TOP, fill=tk.X, pady=5, padx=5)

        # 3. スライダー用フレーム
        slider_frame = ttk.Frame(control_panel)
        slider_frame.pack(side=tk.TOP, fill=tk.X, pady=10, padx=5)

        self.sliders = {}
        # スライダーを縦に配置
        self.create_slider(slider_frame, "Axial (Z)", 0, 0, 0, 0)
        self.create_slider(slider_frame, "Sagittal (X)", 0, 0, 0, 1)
        self.create_slider(slider_frame, "Coronal (Y)", 0, 0, 0, 2)
        
        ttk.Separator(slider_frame, orient=tk.HORIZONTAL).grid(row=3, column=0, sticky="ew", pady=10)
        
        self.create_slider(slider_frame, "WL", -10000, 30000, 0, 4, default_val=40)
        self.create_slider(slider_frame, "WW", 1, 20000, 0, 5, default_val=400)

        # リセットボタン（WL/WW を見やすい値に戻す）
        auto_frame = ttk.Frame(control_panel)
        auto_frame.pack(side=tk.TOP, fill=tk.X, pady=5, padx=5)
        # WL/WW をリセットするボタン（WL/WW のみリセット）
        self.auto_button = ttk.Button(auto_frame, text="WL/WWリセット", command=self.auto_window)
        self.auto_button.pack(fill=tk.X)

        # 専用の表示リセットボタン（読み込みボタンの下）
        self.reset_button = ttk.Button(load_frame, text="表示をリセット", command=self.reset_view)
        self.reset_button.pack(fill=tk.X, pady=(6,0))
        # スライス情報表示ラベル
        self.slice_info = ttk.Label(control_panel, text="スライス: - / -", wraplength=230)
        self.slice_info.pack(side=tk.TOP, fill=tk.X, pady=5, padx=5)

        # ウィンドウリサイズ時のイベントバインド
        self.root.bind("<Configure>", self.update_views_debounced)
        # （マウスホイールでのスライス移動は削除）


    def create_slider(self, parent_frame, text, min_val, max_val, col, row, default_val=0):
        """スライダーとラベルをセットで作成するヘルパー関数 (縦並び用)"""
        frame = ttk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky="ew", pady=2)
        parent_frame.columnconfigure(col, weight=1)

        label_text = f"{text}: {default_val}"
        label = ttk.Label(frame, text=label_text) # width=15 を削除
        label.pack(side=tk.TOP, fill=tk.X) 

        slider = ttk.Scale(frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL, command=self._update_views_logic)
        slider.set(default_val)
        slider.pack(side=tk.TOP, fill=tk.X, expand=True) 
        
        self.sliders[text] = {"slider": slider, "label": label, "label_text": text}

    def load_dicom_folder(self):
        """DICOMフォルダを読み込み、3Dボリュームを構築する"""
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return

        self.status_label.config(text="読み込み中...")
        self.root.update()
        
        self.is_loading = True # --- 【修正点】ロード開始フラグ ---

        slices = []
        try:
            for f in os.listdir(folder_path):
                file_path = os.path.join(folder_path, f)
                if os.path.isfile(file_path):
                    try:
                        ds = pydicom.dcmread(file_path)
                        if ('SliceLocation' in ds or 'InstanceNumber' in ds) and 'PixelData' in ds:
                            slices.append(ds)
                    except Exception:
                        continue

            if not slices:
                raise ValueError("有効なDICOMスライスが見つかりません。")

            if 'SliceLocation' in slices[0]:
                slices.sort(key=lambda x: float(x.SliceLocation))
                sort_criteria = "SliceLocation"
            else:
                slices.sort(key=lambda x: int(x.InstanceNumber))
                sort_criteria = "InstanceNumber"
            
            pixel_data_list = []
            for ds in slices:
                pixels = ds.pixel_array.astype(np.float64)
                slope = float(ds.RescaleSlope) if 'RescaleSlope' in ds else 1.0
                intercept = float(ds.RescaleIntercept) if 'RescaleIntercept' in ds else 0.0
                pixels = pixels * slope + intercept
                pixel_data_list.append(pixels)

            self.volume = np.stack(pixel_data_list, axis=0)
            
            z_max, y_max, x_max = self.volume.shape
            self.update_slider_range("Axial (Z)", 0, z_max - 1)
            self.update_slider_range("Coronal (Y)", 0, y_max - 1)
            self.update_slider_range("Sagittal (X)", 0, x_max - 1)
            # 初期 WL/WW は見やすいプリセット値にする
            preset_wl = 40
            preset_ww = 400
            if "WL" in self.sliders:
                self.sliders["WL"]["slider"].config(from_=-10000, to=30000)
                self.sliders["WL"]["slider"].set(preset_wl)
                self.sliders["WL"]["label"].config(text=f"WL: {preset_wl}")
            if "WW" in self.sliders:
                self.sliders["WW"]["slider"].config(from_=1, to=20000)
                self.sliders["WW"]["slider"].set(preset_ww)
                self.sliders["WW"]["label"].config(text=f"WW: {preset_ww}")
            
            self.status_label.config(text=f"読込完了: {z_max}スライス (基準: {sort_criteria})")
            
            self.notebook.select(0)
            self._update_views_logic() 

        except Exception as e:
            self.status_label.config(text="読み込みエラー")
            messagebox.showerror("エラー", f"DICOMフォルダの読み込みに失敗しました:\n{e}")
            self.volume = None
        
        self.is_loading = False # --- 【修正点】ロード完了フラグ ---

    # マウスホイールでのスライス移動機能は削除しました

    def auto_window(self):
        """WL/WW を見やすいプリセット値に戻す（リセット用）"""
        try:
            wl = 40
            ww = 400
            if "WL" in self.sliders:
                self.sliders["WL"]["slider"].set(wl)
                self.sliders["WL"]["label"].config(text=f"WL: {wl}")
            if "WW" in self.sliders:
                self.sliders["WW"]["slider"].set(ww)
                self.sliders["WW"]["label"].config(text=f"WW: {ww}")
            self._update_views_logic()
        except Exception:
            pass

    def reset_view(self, *args): # *args を受け取れるように
        """【修正】スライス位置のみを初期状態に戻す"""
        if self.volume is None:
            return
            
        z_max, y_max, x_max = self.volume.shape
        
        # 1. スライダーを中央に戻す
        if "Axial (Z)" in self.sliders:
            self.sliders["Axial (Z)"]["slider"].set((z_max - 1) // 2)
        if "Coronal (Y)" in self.sliders:
            self.sliders["Coronal (Y)"]["slider"].set((y_max - 1) // 2)
        if "Sagittal (X)" in self.sliders:
            self.sliders["Sagittal (X)"]["slider"].set((x_max - 1) // 2)
        
        # 2. WW/WLのリセット処理を削除
        
        # 3. タブをAxialに戻す
        try:
            self.notebook.select(0)
        except Exception:
            pass
            
        self.status_label.config(text="スライス位置をリセットしました")
        
        # 4. 表示を更新
        self._update_views_logic()

    def fit_all_views(self):
        pass

    def update_slider_range(self, name, min_val, max_val):
        if name in self.sliders:
            slider = self.sliders[name]["slider"]
            slider.config(from_=min_val, to=max_val)
            default_val = (min_val + max_val) // 2
            slider.set(default_val)
            self.sliders[name]["label"].config(text=f"{self.sliders[name]['label_text']}: {default_val}")

    def apply_window(self, image_data, window_level, window_width):
        min_val = window_level - (window_width / 2)
        max_val = window_level + (window_width / 2)
        windowed_image = np.clip(image_data, min_val, max_val)
        
        if window_width > 0:
            normalized_image = ((windowed_image - min_val) / window_width) * 255.0
        else:
            normalized_image = np.zeros_like(windowed_image)
            
        return normalized_image.astype(np.uint8)

    def resize_with_aspect_ratio(self, pil_img, container_w, container_h):
        img_w, img_h = pil_img.size
        if img_w == 0 or img_h == 0 or container_w <= 1 or container_h <= 1:
            return Image.new("L", (1, 1), 0), (0,0), (0,0)

        scale = min(container_w / img_w, container_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        try:
            resized_img = pil_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
        except AttributeError:
            resized_img = pil_img.resize((new_w, new_h), Image.BILINEAR)

        final_img = Image.new("L", (container_w, container_h), 0)
        
        paste_x = (container_w - new_w) // 2
        paste_y = (container_h - new_h) // 2
        final_img.paste(resized_img, (paste_x, paste_y))
        
        return final_img, (paste_x, paste_y), (new_w, new_h)


    def update_views_debounced(self, *args):
        """【ウィンドウリサイズ専用】デバウンス用ラッパー"""
        
        # --- 【修正点】ロード中はリサイズイベントを無視 ---
        if self.is_loading:
            return
            
        if self.debounce_job:
            self.root.after_cancel(self.debounce_job)
        self.debounce_job = self.root.after(150, self._update_views_logic)

    def _update_views_logic(self, *args):
        """【実際の描画処理】スライダー操作時とリサイズ完了時に呼ばれる"""
        
        if self.volume is None:
            return

        try:
            z_slice = int(self.sliders["Axial (Z)"]["slider"].get())
            x_slice = int(self.sliders["Sagittal (X)"]["slider"].get())
            y_slice = int(self.sliders["Coronal (Y)"]["slider"].get())
            wl = int(self.sliders["WL"]["slider"].get())
            ww = int(self.sliders["WW"]["slider"].get())
            
            for name, slider_info in self.sliders.items():
                val = int(slider_info["slider"].get())
                slider_info["label"].config(text=f"{slider_info['label_text']}: {val}")

            # スライス情報更新
            try:
                z_slice = int(self.sliders["Axial (Z)"]["slider"].get())
                total = self.volume.shape[0]
                self.slice_info.config(text=f"Axial: {z_slice} / {total-1}")
            except Exception:
                pass

            axial_img = self.volume[z_slice, :, :]
            sagittal_img = self.volume[:, :, x_slice]
            coronal_img = self.volume[:, y_slice, :]
            
            axial_norm = self.apply_window(axial_img, wl, ww)
            sagittal_norm = self.apply_window(sagittal_img, wl, ww)
            coronal_norm = self.apply_window(coronal_img, wl, ww)
            
            # 1. Axial (Canvas)
            canvas_w = self.axial_canvas.winfo_width()
            canvas_h = self.axial_canvas.winfo_height()
            pil_axial = Image.fromarray(axial_norm)
            final_axial_img, offset, new_size = self.resize_with_aspect_ratio(pil_axial, canvas_w, canvas_h)
            self.tk_images["axial"] = ImageTk.PhotoImage(image=final_axial_img)
            self.axial_canvas.delete("all")
            self.axial_canvas.create_image(0, 0, anchor='nw', image=self.tk_images["axial"])
            
            img_offset_x, img_offset_y = offset
            img_new_w, img_new_h = new_size
            if img_new_w > 0 and img_new_h > 0:
                y_ratio = y_slice / self.volume.shape[1]
                x_ratio = x_slice / self.volume.shape[2]
                line_y = img_offset_y + (y_ratio * img_new_h)
                line_x = img_offset_x + (x_ratio * img_new_w)
                self.axial_canvas.create_line(img_offset_x, line_y, img_offset_x + img_new_w, line_y, fill='red', width=1)
                self.axial_canvas.create_line(line_x, img_offset_y, line_x, img_offset_y + img_new_h, fill='red', width=1)

            # 2. Sagittal (Label)
            label_w = self.sagittal_label.winfo_width()
            label_h = self.sagittal_label.winfo_height()
            pil_sagittal = Image.fromarray(sagittal_norm)
            final_sagittal_img, _, _ = self.resize_with_aspect_ratio(pil_sagittal, label_w, label_h)
            self.tk_images["sagittal"] = ImageTk.PhotoImage(image=final_sagittal_img)
            self.sagittal_label.config(image=self.tk_images["sagittal"])

            # 3. Coronal (Label)
            label_w = self.coronal_label.winfo_width()
            label_h = self.coronal_label.winfo_height()
            pil_coronal = Image.fromarray(coronal_norm)
            final_coronal_img, _, _ = self.resize_with_aspect_ratio(pil_coronal, label_w, label_h)
            self.tk_images["coronal"] = ImageTk.PhotoImage(image=final_coronal_img)
            self.coronal_label.config(image=self.tk_images["coronal"])

        except Exception as e:
            # print(f"描画更新エラー: {e}") # デバッグ用
            pass

# --- アプリケーションの実行 ---
if __name__ == "__main__":
    root = tk.Tk()
    app = DicomViewerApp(root)
    root.bind("<Configure>", app.update_views_debounced) 
    root.mainloop()