# Matrix Six v0.6 — JLCPCB見積もり

修正済み裏面SD／LiPo／充電／電源切替を含む48部品の両面実装用データです。旧v0.5のBOM/CPL・Gerberとは混用できません。注文・決済は未実施です。

- [Gerber ZIP](Matrix6-v0.6-Gerber.zip)
- [JLCPCB BOM](assembly/Matrix6-v0.6-BOM.csv) / [CPL](assembly/Matrix6-v0.6-CPL.csv)
- [出力の照合結果](assembly/export-validation.json) / [元CADとファイルのハッシュ](source-manifest.json)
- [ドリル表](review/drill-report.txt) / [製造指示](review/Matrix6-fabrication-requirements.svg)

基板5枚、実装2枚を見積もります。FR-4・4層・1.6 mm・紫・ENIG・外層1 oz／内層0.5 oz、JLC04161H-7628相当、USB差動90 Ωを指定。U1/U2のサーマルビアを平坦に充填・銅キャップし、コネクタの部品穴は開口を保持します。

Top 37部品、Bottom 11部品。J3とH1/H2はスルーホール接続を含みます。ヘッダーとSD/JSTの配置原点は本体中心に補正しています。モデルの回転・極性はJLCPCB実装プレビューで確認が必要です。

現在のBOMでLCSC番号が空欄の部品は、ライブ画面で型番と定格を照合します。充電器は4.2 V版、SDはDM3AT-SF-PEJM5、LiPoコネクタはPH2・1番BAT+／2番GND。両面実装費、挿入実装、メーカー在庫と製造者のCAM確認を含む最終価格はサイトで確定します。
