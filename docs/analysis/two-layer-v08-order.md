# v0.8 2層版の発注準備（2026-09-08）

中央文字・R8移動を含むCADコミット `d0ea1e0` のGerber、BOM、CPLをJLCPCBへ新規アップロードし、決済画面まで準備しました。支払い完了と製造承認は確認していません。

- 注文番号：`W2026090808083223`
- PCB：`Y263-2423180A`
- PCBA：`SMT026090860012-2423180A`
- アップロード識別子：`457b67c9c2a34bfcb186788817f25ab9`
- Gerber SHA-256：`89d3072399df033898e433e7c2f0e9a7e75ffe56867b2b2d70deb4cf3636ab8f`
- PCB SHA-256：`20be22f195de4a42cf2f9902171f88ed01ce740b4684df816ad5f17b66c79c9f`

## 数量・条件

基板5枚、Standard両面実装2枚。2層・公称1.6 mm・両面1 oz・紫・白シルク・S1000H TG155・ENIG 1u。原板40.64 × 61 mm、JLC追加レール込み70.64 × 71 mm。最小穴径0.3 mm料金区分、エポキシ充填・銅キャップ、Horizontal Electroless Copper Plating、フライングプローブ全数検査。製造図面・実装配置の確認あり、自動承認しない設定を選択しました。

26 BOMグループ、48部品（表37／裏11）は全て指定型番のまま選択済み。USB J1（C5184243）も数量2・選択済みを確認しました。BOM再読込み後は26種類検出・26種類確認済み、全26行が選択済みでした。部品置換は行っていません。在庫は確認時点の情報で、製造開始を保証するものではありません。

JLCの表裏プレビューで中央文字、R8のモジュール右側配置、縦のH1/H2、裏面microSDを確認しました。一部JLC 3Dモデル（U1/J1/J3等）の原点に差があるため、外観だけを根拠にCPL座標を変更していません。CAD実装基準図・表裏3D画像を添付し、全パッド・極性とSD挿入口を実装担当者が照合するよう備考に指定しました。JLCの最終DFM/CAM配置承認は未実施です。

## 決済画面の表示額

| 項目 | USD |
|---|---:|
| 基板5枚 | 83.27 |
| 部品・両面実装2枚 | 162.40 |
| 商品合計 | 245.67 |
| DHL Express送料 | 18.38 |
| PCBAクーポン | -6.00 |
| **決済画面合計** | **258.05** |

支払方法は利用者によるカード入力中で、こちらから決済操作はしていません。支払い完了は未確認です。OCSの見積表示は8.79ドルでしたが、最終確認した決済画面ではDHL（1–3営業日）が選択されていました。

レール除去費2.30ドルは上記合計に含まれず、実装備考に伴う追加費用も審査後確定です。輸入税・通関手数料等は配送条件に従います。製造日数表示は基板3日・実装4–5日、追加オプションで1日追加。カートの出荷目安は2026-09-16でしたが、支払い・資料確認・審査により変わります。

## 保存した備考

PCB備考（196文字）：

> See fabrication JPG in ZIP. Fill/copper-cap thermal/in-pad vias incl.12 U1 pad41 PTHs (not leads). Keep connector holes/slots/NPTH open. Preserve USB coplanar GND. 2L,1.6mm. CAM approval required.

実装備考（442文字）：

> Matrix Six v0.8: centered logo and moved R8. Assemble all 48 parts (37 top/11 bottom). Match attached CAD/CPL pads and polarity; U1/J1/J3 web 3D origins may differ. H1/H2 vertical. J2 bottom microSD mouth faces antenna/top; keep withdrawal corridor clear. J3 bottom, pin1 BAT+, pin2 GND. CPL rotation corrections are already included. Remove rails without damaging antenna/USB/SD. Send placement preview for customer approval before assembly.

添付：`Matrix6-assembly-reference.png`、`pcb-3d-top.png`、`pcb-3d-bottom.png`。製造条件JPGはアップロード済みGerber ZIPにも含まれます。

旧4層v0.7注文 `W2026090719552210` は別注文として残り、今回変更・キャンセル・支払いをしていません。2層試作版は管理インピーダンス保証を前提にせず、実機USB・電源・熱試験は引き続き必要です。

出典：[最新注文の決済ページ](https://trade.jlcpcb.com/checkout/payMethod?systemType=order_pcb&calType=PAY&batchNum=W2026090808083223)、[アップロード済みPCBA](https://cart.jlcpcb.com/smt-order/?pcbFileNo=457b67c9c2a34bfcb186788817f25ab9)。
