# Matrix5シールド互換性 — Matrix Six v0.6

Matrix5 MainのJ4/J5と同じ順序で、Matrix6のH1/H2を配線しました。ピッチ2.54 mm、各20ピン、列間33.02 mmです。表面から見てH1が左、H2が右、**1番ピンはUSB側**です。旧DevBoard v0.4の30.48 mmヘッダーとは互換ではありません。

照合元は、2026-09-07に読み取り専用APIで取得したEasyEDAの `MatrixFive_Main_PCB` とS1〜S11の実設計です。公開されている製造ZIPの `FlyingProbeTesting.json` でも位置・使用ピンを照合しました。公開側の基準コミットは [Matrix5 4e5bad0](https://github.com/FaBoAI/Matrix5/tree/4e5bad09b81449c644275b11321cdfa5019caf93) です。抽出した[Mainの端子表](reference/matrix5-pinout.json)と[シールドの使用端子](reference/matrix5-shield-interface.json)を保存しています。

## 端子表

| ピン | H1 | H2 |
|---:|---|---|
| 1 | 3V3出力 | VBUS出力（F1保護後） |
| 2 | GND | GND |
| 3 | EN | GPIO17 |
| 4 | GPIO0 / BOOT | GPIO18 |
| 5 | GPIO1 | NC：Matrix5ではUSB D− |
| 6 | GPIO2 | NC：Matrix5ではUSB D＋ |
| 7 | GPIO3 | GPIO21 / S1 DATA |
| 8 | GPIO4 | GPIO38 |
| 9 | GPIO5 | GPIO39 |
| 10 | GPIO6 | GPIO40 |
| 11 | GPIO7 | GPIO41 |
| 12 | GPIO8 | GPIO42 |
| 13 | GPIO9 | GPIO45 |
| 14 | GPIO10 | GPIO46 |
| 15 | GPIO11 / MOSI / SDA | GPIO47 |
| 16 | GPIO12 / SCLK / SCL | GPIO48 / 青LED |
| 17 | GPIO13 / MISO | GPIO44 / RX |
| 18 | GPIO14 / HEAT_EN | GPIO43 / TX |
| 19 | GPIO15 | GND |
| 20 | GPIO16 | VBAT（J3の電池端子） |

**38端子の信号・電源を合わせ、USB D±の2端子は意図的に未接続です。** H2.20をVBATへ接続しました。確認した11シールドの使用端子は一致しています。SDはGPIO10〜13を共有します。GPIO11/12をI2Cとして使うときなど、カードと競合する構成ではカードを抜いてください。

## シールド別の照合範囲

| シールド | 照合した機能 | 使用端子数 |
|---|---|---:|
| S1 WS2812 6×6 | H2.7のGPIO21、VBUS、GND | 5 |
| S2 ICM20948 | GPIO1〜9のCS、SPI、3V3、GND | 16 |
| S3 BME690 | GPIO1〜9のCS、SPI、3V3、GND | 16 |
| S4 MLX90393 | GPIO1〜9のCS、SPI、3V3、GND | 16 |
| S5 VL53L1X | GPIO1〜9のXSHUT、I2C、3V3、GND | 15 |
| S6 BMP581 | GPIO1〜9のCS、SPI、3V3、GND | 16 |
| S7 VL6180X | GPIO1〜9のCE、I2C、3V3、GND | 15 |
| S8 Touch | GPIO1〜9 | 9 |
| S9 MagPix | GPIO1〜9、VBUS、GND | 13 |
| S10 AirFlow | GPIO1〜9、GPIO14、3V3、VBUS、GND | 15 |
| S11 Display | GPIO1〜4、MOSI/SCLK、3V3、VBUS、GND | 11 |

各シールド40か所のパッド座標と上表の使用端子を、保存したKiCad PCBに対して検査しています。[検証結果](validation/matrix5-compatibility.json)はピン配置の一致を示すもので、実物を積層して通電した結果ではありません。S2/S4/S6/S9はMatrix5側の改版履歴にも従ってください。

## 機械寸法と取り付け

Matrix6は40.64 × 61.00 mm。H1.1=(101.27,153.26)、H2.1=(134.29,153.26) mmで、番号が増える方向はKiCad上で−Yです。標準シールド40.64 × 53.34 mmを重ねると、外形はX=97.46〜138.10、Y=102.46〜155.80 mmとなります。USBとRESET/BOOTはその下側に残ります。S11は長い基板のため、外形全体はこの範囲を超えます。

H1/H2は表面の1×20メスソケット用フットプリントです。ソケット・オスピン・スペーサーの組合せは、シールド裏面の部品とMatrix6のESP32モジュール等の高さを実測して決めてください。ヘッダーのXY一致だけで積層高さや筐体への適合は保証できません。アンテナ上を金属や別基板で覆わず、積層した状態の無線性能も確認します。

## 電源・ファームウェアの条件

- I/Oは3.3 V。S1へ出すGPIO21も3.3 Vで、追加の5 Vレベル変換はありません。S1実装LEDの入力閾値と波形を試作で確認してください。
- 3V3の計算条件はMCU・SDと外部負荷の**合計500 mA**。これにVBUSシールド負荷**100 mA**とLiPo充電100 mAを追加した場合を計算しました。VBUSはF1の後、D1の前から供給します。
- 電池時はH2.1の5 V出力を供給しません。J3は1番BAT+・2番GND、保護付き1S 3.7 V／4.2 V LiPo用です。
- H1.1/H2.1は出力です。H2.1へ外部電源を直接接続するとUSB側へ逆給電できます。F1は逆流防止素子ではありません。
- S1の全点灯、S9の複数コイル駆動、S10のヒーター等は上記電源条件で保証していません。外部電源を使うシールドは、そのシールドの電源切替・逆流防止設計に従います。
- GPIO0/3/45/46は起動条件に関係するため、リセット中のシールド側の負荷・プル抵抗を確認します。青LEDはGPIO48です。
- Matrix5のSPI/I2C/CS/DATA番号はそのまま使えます。シールドに対応するファームウェアを選び、給電を切ってから交換してください。ファームウェアの移植・実機動作試験はこのコミットには含みません。

## 電気的な検証

[DRC](validation/drc.json)、[ERC](validation/erc.json)、未配線、回路図整合性はすべて0件。オートルーターは使わず、個別の配線座標を指定しました。USBの銅配線はv0.4と同一、表面のみ・ビア0、A側の幾何長合わせにはR11の1.65 mmパッド間距離を含みます。

L2は連続したGND 1領域、USB直下13,182点の欠損0。USB本体下の表面配線・ビア・ベタは0で、禁止領域に試験用配線を入れた一時コピーでは2件の禁止違反を検出しました。[USB禁止領域の検証](validation/usb-keepout-validation.json)

3.3 V配線の電圧降下は500 mAでモジュールまで53.5 mV、H1まで31.4 mV。L2の戻り経路は新しいU2のGNDビアへ再計算しました。周囲50℃・効率80%などの仮定による計算であり、実測値ではありません。層構成はJLC04161H-7628相当の4層、USB均一断面の既存2D推定は約91.1 Ω。製造者のインピーダンス承認、TDR、電源負荷・温度・実効容量、積層状態の動作は試作で確認します。[電源・配線計算](validation/electrical-audit.json)、[GND計算](validation/ground-plane-dc.json)
