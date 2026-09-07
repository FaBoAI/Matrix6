# ESP32-S3 DevBoard v0.4 — USB本体下配線退避版

このフォルダーが現在の作業版です。[KiCadプロジェクト](ESP32-S3-DevBoard.kicad_pro)をKiCad 10で開いてください。2026-09-07、KiCad 10.0.6で確認しました。

ESP32-S3-WROOM-1-N8R8、USB-CネイティブUSB、35.56 × 61 mm、4層基板です。RESETはUSBの左、BOOTは右。下側の赤LEDは `POWER`、青LEDは `PIN 48` です。配線は座標を指定して個別に作成・修正しており、オートルーターは使用していません。

表面中央に `Designed By GPT-6 Astra` を1行のシルク文字として追加しました。文字高さ1.0 mm、線幅0.15 mmです。3D表示へ反映し、文字追加後のDRCも0件です。

| 項目 | v0.4の結果 |
| --- | --- |
| USB配線 | F.Cu・ビア0。B側は銅配線等長、A側は追加0ΩジャンパーR11の端子間距離を含む幾何長差0.1 mm以内 |
| USBインピーダンス | 層構成を設定、均一断面の独立2D計算で91.1 Ω |
| USB本体下 | 配線・ビア・表面ベタを撤去。フットプリントに禁止領域を登録し、DRC検出を試験済み |
| L2 GND | 信号配線0、連続した1領域。USB直下13,182点の欠損0 |
| 3.3 V電源 | AP63203降圧回路へ変更、主配線0.8 mm、出力コンデンサ2個 |
| 電圧降下 | 500 mAで出力配線33.9 mV、L2戻りプレーン約1.4 mV（計算） |
| 発熱 | 周囲50℃、効率80%、熱抵抗150℃/Wを仮定し接合温度111.9℃ |
| DRC / 未配線 / 回路図整合性 / ERC | すべて0件。A側は部品をまたぐ独立経路計算で検証 |

電源の設計条件は **3.3 V側合計500 mA連続・周囲50℃・負荷時USBコネクタ電圧4.75 V以上** です。IC単体の2 A定格はこの基板の定格ではありません。ヘッダ外部負荷も同じ総電流枠に含みます。

**D＋とCC1をUSBコネクタ本体下から退避しました。** 表面配線・ビア・ベタの禁止領域を登録し、故意に違反を入れた一時コピーでDRC検出も確認しています。R11（Vishay CRCW06030000Z0EA、0603 0Ω）はUSBのA6枝に必須です。A側の幾何学的な長さ合わせにはR11のパッド中心間1.65 mmを含めます。パッケージの電気長やUSBアイパターンの実測保証ではありません。インピーダンスTDR、電源の実測温度・効率・負荷過渡、コンデンサの実効容量は引き続き試作／部品確定時に確認します。

詳細な計算条件・層厚・部品変更・残確認は [電気設計レビュー](electrical-review.md) に記載しました。発注データの提出・部品の在庫照合・実基板試験は実施していません。

- [回路図](review/schematic-final.png)
- [3D表示（傾斜30°）](review/pcb-3d-v04.png)
- [表面配線](review/pcb-top-v04.png) / [L2 GND](review/pcb-L2-GND-v04.png) / [L3](review/pcb-L3-v04.png) / [裏面](review/pcb-bottom-v04.png)
- [DRC結果](drc-final.json) / [ERC結果](erc-final.json) / [禁止領域検証](review/usb-keepout-validation.json)
- [配線・GND・電源計算](review/electrical-audit.json)
- [USBコネクタ下の配線図](review/usb-connector-review.png) / [照合結果](review/usb-connector-review.json)

## 編集と再現

通常はこのフォルダーのKiCadファイルを編集します。親フォルダーの同名ファイルとv0.2 ZIPは以前の履歴です。旧チェック画像や旧レポートは配布ZIPに含めていません。

`../scripts/fix_usb_underbody.py` は `../review/pre-usb-keepout-v03` の保存済み入力から今回の回路図・PCB・禁止領域を生成します。`upgrade_buck.py` は旧v0.3の生成記録です。再実行すると、その後に行ったGUI編集を置き換えます。`complete_electrical_layout.py` はそれ以前のUSB/GND/電源配線修正の記録です。いずれも配線座標を明示したスクリプトです。

`verify_project.py` はERCとDRCを実行します。`audit_electrical_layout.py` と `export_ground_geometry.py` は保存されたPCBをKiCad Pythonで読み込みます。`usb_cross_section.py` と `ground_plane_dc.py` はNumPy/SciPy/Shapely/Matplotlibを使う独立数値計算です。実行環境・コマンドは電気設計レビューを参照してください。

`DevBoard.pretty` と `fp-lib-table` をプロジェクトと一緒に保管してください。モジュールのアンテナ張り出し用とUSBコネクタの禁止領域付きフットプリントを含みます。標準ライブラリのパッド位置・寸法は変更していません。
