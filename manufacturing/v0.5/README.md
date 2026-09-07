# Matrix6 v0.5 — JLCPCB試作発注準備

対象CADはコミット `d1438c606553286f8075416b602664ae09d1bd65`。CAD自体は変更していません。発注・決済は未実施です。

## アップロードするファイル

**[Matrix6-v0.5-Gerber.zip](Matrix6-v0.5-Gerber.zip)** をPCBのアップロード欄で使用します。4銅層、表裏レジスト・シルク・ペースト、外形、PTH/NPTHのExcellon、インピーダンス／穴埋めの指示JPGを含みます。`review/` のファイルを実装用BOM/CPLとしてそのまま提出しないでください。

JLCPCBのGerber解析では4層・40.64 × 61.00 mmと認識されました。これは製造指示JPG追加前の解析確認です。JPGを追加した現行ZIPはログイン後に再アップロードしてください。詳細なGerber Viewerと部品検索はログイン画面へ遷移するため、アカウントでの確認が残っています。見積もりは画面上で確認した仮条件で、カート保存・注文は未実施です。

## 見積もり条件（仮に基板5枚）

| 項目 | 条件 |
|---|---|
| 外形・枚数 | 40.64 × 61.00 mm、単片、5枚 |
| 層数・板厚 | 4層、呼称1.6 mm |
| 層構成 | JLC04161H-7628 |
| 材料 | FR4 Tg155（0.2 mm穴の選択時にサイトが自動設定） |
| 銅厚 | 外層1 oz、内層0.5 oz |
| 色・表面処理 | 紫・白シルク、ENIG 1 µin |
| インピーダンス | USB差動90 Ω ±10%、L1信号 / L2 GND参照 |
| 最小穴径 | 0.2 mm（U1の熱パッド内に12個） |
| 穴処理 | Epoxy Filled & Capped。熱パッド内のはんだ吸い込みを抑えるために選択 |
| 電気検査 | Flying Probe、サイトが追加した4-Wire Kelvin Test |
| 製造データ確認 | Yes |

2026-09-07の画面見積もりは**基板5枚 US$119.35**。内訳は基板7.00、ENIG16.80、紫5.00、インピーダンス32.84、製造データ確認1.04、穴埋め16.72、最小穴16.72、材料3.34、Kelvin検査16.58、Via Plating Method 3.31 USDです。部品代・実装費・送料・税・クーポンは含みません。ログイン後の実際の注文内容で再計算します。

最初に表示されたUS$62.68は、0.2 mm穴と穴埋め関連条件を反映する前の金額です。最終金額として使用しないでください。

## CAM確認に使う情報

- [製造指示JPG](gerber/Matrix6-fabrication-requirements.jpg)：90 Ωの対象配線、層順、線幅0.28 mm／間隔0.20 mm／表面GND間隔0.50 mm、穴処理。
- PTHは186個。0.2 mm熱パッド穴12、0.3 mmビア130、1.0 mmヘッダー穴40、0.6 mm工具のUSB長穴4。NPTHは0.65 mmが2個。[穴あけレポート](review/drill-report.txt)
- 0.2 mm穴はU1 pad 41の熱ビアです。ヘッダーの1.0 mm穴、USBの長穴、位置決めNPTHは穴埋めしません。CAMに分類と仕上がりを確認します。
- JLCPCB側の材料・エッチング補正による線幅調整と、試験クーポン／測定レポートを製造指示に依頼しています。現在の約91.1 Ωは設計上の2D推定で、製造承認ではありません。
- 「Confirm Production file」は永続的な製造保留を保証する設定ではありません。サイト説明ではUS$300未満の注文は48時間以内に確認しないと自動的に製造へ進む場合があります。

## 部品実装は未リリース

`review/Matrix6-KiCad-BOM-DRAFT.csv` と `review/Matrix6-KiCad-positions.csv` は、保存済みCADから出した**32部品の確認用データ**です。JLCPCB用の部品番号、部品ごとの回転補正、実装対象はまだ確定していません。今回のZIPにBOM/CPLは含めていません。

ESP32-S3-WROOM-1-N8R8はJLCPCBの **C2913201 / Standard Only** を確認しています。閲覧時の在庫4,792、Available Order Qty 4,533で、在庫確保・購入は行っていません。[部品ページ](https://jlcpcb.com/partdetail/3198299-ESP32_S3_WROOM_1N8R8/C2913201)

USB4105-GF-A-120は [C5184243](https://jlcpcb.com/partdetail/GCT-USB4105_GF_A120/C5184243)、SS14-E3/61Tは [C47460](https://jlcpcb.com/partdetail/VishayIntertech-SS14_E361T/C47460)、ST製USBLC6-2SC6は [C7519](https://jlcpcb.com/partdetail/C7519) と品番を照合済みです。これらの発注可能数量はBOM照合画面で再確認します。

残作業：抵抗・コンデンサ・LED・メスソケットのメーカー品番決定、全品のJLCPCB実装在庫確認、C1/C2/C8の実効容量確認、ヘッダーの高さ／実装方法、全32部品の回転・極性照合、総額・納期・配送先の確認。F1/R11など既指定部品の代替品を、未確認のまま自動採用しません。

実装付きならStandard PCBAで進めます。シールド互換性・給電条件・試作での確認事項は [互換性資料](../../docs/matrix5-compatibility.md) を参照してください。

## 再生成

`python3 scripts/export_jlcpcb.py` は、検証済みCADのSHA-256を確認してからCLI出力を生成します。製造指示SVGをJPEGにレンダリングし、`scripts/package_jlcpcb.py` でZIPとハッシュを更新してください。CADを編集した場合は、まずプロジェクトの検証と部品・製造条件の再確認が必要です。
