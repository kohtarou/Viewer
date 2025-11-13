# DICOM 3断面ビューア



## 概要

[cite_start]CTやMRIなどで撮影されたDICOMファイル（一連の輪切り画像）が格納されたフォルダを読み込み、以下の3つの断面をインタラクティブに表示・観察するためのアプリケーションです。 [cite: 5]

* [cite_start]**Axial (アキシャル):** 上から見た断面（元の輪切り画像） [cite: 6]
* [cite_start]**Sagittal (サジタル):** 横から見た断面（再構成画像） [cite: 8]
* [cite_start]**Coronal (コロナル):** 正面から見た断面（再構成画像） [cite: 7]

## 導入 (インストール)



[cite_start]本アプリは、実行ファイル（.exe）を起動して使用できます。 [cite: 10]

1.  [cite_start]GitHub リポジトリ ( https://github.com/kohtarou/Viewer ) の右側にある「Releases」セクションにアクセスします。 [cite: 12]
2.  [cite_start]「Assets」の中から「dicom_viewer.exe」をクリックしてダウンロードします。 [cite: 14]
3.  [cite_start]ダウンロードした.exeファイルをダブルクリックして実行します。 [cite: 15]

## 基本的な使い方



### DICOM フォルダの読み込み



1.  [cite_start]アプリ起動後、右上にある **[DICOM フォルダ読込]** ボタンをクリックします。 [cite: 56]
2.  [cite_start]フォルダ選択ダイアログが表示されます。 [cite: 64] [cite_start]観察したいCT画像シリーズ（多数の.dcmファイルが保存されているフォルダ）を選択し、[フォルダーの選択] をクリックします。 [cite: 64]
3.  [cite_start]読み込み完了後、右側のステータス欄に「読込完了: (スライス枚数)」と表示され、左側の画像パネルに画像が表示されます。 [cite: 88]

## 画面の見方と操作方法



[cite_start]アプリ画面は、「画像パネル（左側）」と「操作パネル（右側）」の2つの主要領域で構成されます。 [cite: 105]

### 画像パネル (左側)



* **上段 (Axial):**
    * [cite_start]Axial（上から見た断面）画像が表示されます。 [cite: 125]
    * [cite_start]表示中のSagittal断面とCoronal断面の位置を示す赤い十字線が表示されます。 [cite: 125, 126]
        * [cite_start]**縦線:** Sagittal 断面の現在位置 [cite: 127]
        * [cite_start]**横線:** Coronal 断面の現在位置 [cite: 128]
* **下段 (Sagittal / Coronal):**
    * [cite_start]タブインターフェースにより、Sagittal（横から）とCoronal（正面から）の表示を切り替えることが可能です。 [cite: 130, 131]

### 操作パネル (右側)



[cite_start]すべての操作は右側のパネルで行います。 [cite: 136]

#### スライス位置の調整



[cite_start]3つのスライダーにより、各断面の表示位置をリアルタイムで変更できます。 [cite: 151]

* **Axial (Z) スライダー:**
    * [cite_start]上段の Axial 画像を、Z軸方向（頭側↔足側）にスライス移動させます。 [cite: 154, 155]
    * [cite_start]スライダー下のラベルには、現在のスライス番号と総スライス枚数が表示されます。 [cite: 155]
* **Sagittal (X) スライダー:**
    * [cite_start]下段の Sagittal 画像を、X軸方向（右側↔左側）にスライス移動させます。 [cite: 156, 157]
    * [cite_start]このスライダーの操作は、Axial 画像上の縦の赤線と連動します。 [cite: 157]
* **Coronal (Y) スライダー:**
    * [cite_start]下段の Coronal 画像を、Y軸方向（背中側↔お腹側）にスライス移動させます。 [cite: 158, 159]
    * [cite_start]このスライダーの操作は、Axial 画像上の横の赤線と連動します。 [cite: 159]

#### 表示(コントラスト)の調整 (WW / WL)



[cite_start]観察対象の組織（骨、肺、軟部組織など）に応じて、表示の「明るさ」と「コントラスト」を調整します。 [cite: 161] [cite_start]この調整は、Axial, Sagittal, Coronal のすべての画像に同時に適用されます。 [cite: 161]

* **WL (Window Level) スライダー:**
    * [cite_start]表示する「明るさの中心」を調整します。 [cite: 162, 163]
* **WW (Window Width) スライダー:**
    * [cite_start]表示する「コントラスト（明暗の幅）」を調整します。 [cite: 164, 165]
    * [cite_start]**狭くする（左へ）:** コントラストが強くなります（狭い範囲のCT値のみを表示）。 [cite: 166]
    * [cite_start]**広くする（右へ）:** コントラストが弱くなります（広い範囲のCT値を表示）。 [cite: 167]

#### リセット機能



* **[表示をリセット] ボタン:**
    * [cite_start]Axial, Sagittal, Coronal のスライス位置を、ボリュームデータの中央に戻します。 [cite: 170, 171]
* **[WL/WW リセット] ボタン:**
    * [cite_start]WW/WLの値を、軟部組織の標準設定（WL: 40, WW: 400）に戻します。 [cite: 172, 173, 174]

## レイアウトの調整



[cite_start]アプリの各領域の境界線（仕切り線）は、マウスでドラッグすることにより、自由にサイズを変更できます。 [cite: 176]

1.  [cite_start]**左右の調整:** 画像パネルと操作パネルの間の縦の仕切り線を左右にドラッグします。 [cite: 177]
2.  [cite_start]**上下の調整:** Axial 画像と下のタブ（Sagittal/Coronal）の間の横の仕切り線を上下にドラッグします。 [cite: 178]

## 作成者

* [cite_start]4年1コース 18番 中尾晃太朗 [cite: 3]