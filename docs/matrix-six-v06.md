# Matrix Six v0.6

SDスロットの口の前にLiPoコネクタ・充電部品が来ていた配置を修正しました。J2を反転し、口をアンテナ側（KiCadの−Y）へ向けています。裏面のX=109.9〜125.7、Y=100.5〜123.0 mmは部品配置禁止領域です。標準フットプリント内の金属接触部の銅箔禁止領域も維持しています。全裏面部品のコートヤードとこの通路の重なりは0です。[寸法図](validation/sd-access.svg)、[数値検証](validation/sd-access.json)

名前をMatrix Sixに変更し、SDとLiPo回路を追加しました。USBの銅配線・本体下禁止領域、4層スタックアップ、L2の連続GND、40か所のシールドヘッダー位置は保持しています。自動配線は使用していません。新規配線は `scripts/revise_matrix_six.py` と `scripts/matrix_six_rear_routes.py` に明示した座標です。

## 回路

- SD: Hirose DM3AT-SF-PEJM5。CS=IO10、MOSI=IO11、CLK=IO12、MISO=IO13。CMDとDAT0〜3は各10 kΩで3V3へプルアップ。検出接点は未接続。SPI 20 MHz以下を立ち上げ条件とし、最初は低速で書き込み・読み出しとWi-Fi併用時の安定性を確認します。[Espressifのプルアップ要件](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/peripherals/sd_pullup_requirements.html)
- 3V3: TPS63001DRCR、SRN4018-2R2M（2.2 µH）。VINAは100 Ωと100 nFでフィルタ。入力22 µF、出力22 µF×2。L2に信号は配線していません。[TIデータシート](https://www.ti.com/lit/ds/symlink/tps63000.pdf)、[Bourns](https://www.bourns.com/docs/product-datasheets/srn4018.pdf)
- 充電: MCP73831T-2ACI/OT、RPROG=10 kΩで公称100 mA。1S 4.2 V用。充電器のSTATは未使用で、LEDは指定の赤POWERと青PIN 48の2個です。[Microchipデータシート](https://ww1.microchip.com/downloads/en/DeviceDoc/20001984g.pdf)
- 電源切替: USB→D1→VSYS、電池→AO3401A→VSYS。PMOSのゲートをUSBへ、ドレインを電池、ソースをVSYSへ接続。電池負荷を充電端子から分離します。[Microchip AN1149](https://ww1.microchip.com/downloads/en/AppNotes/01149c.pdf)、[AO3401A](https://www.aosmd.com/pdfs/datasheet/AO3401A.pdf)
- 電池端子: JST S2B-PH-K-S(LF)(SN)。1番VBAT、2番GND。H2.20もVBATです。保護回路付き3.7 V／4.2 V、500 mAh以上、1 A以上の放電定格を基準としました。電池未接続でもUSBで動作する構成です。逆極性防止、セル温度センサー、3 Vでの電池遮断はありません。電池側の保護と仕様に従います。

## 検証と残る確認

ERC、全重大度のDRC、未配線、回路図等価性は0。USBは表面のみ・ビア0、v0.4と同じ銅形状。L2は1領域で、USB直下13,182サンプルに欠損がありません。Matrix5の11シールドの使用端子は一致します。

電源の計算条件は、周囲50℃、3V3の合計500 mA、USB時は追加VBUS負荷100 mAと充電最大110 mA、電池時は入力800 mAでのスクリーニングです。3V3の配線降下はモジュールまで約53.5 mV、H1まで約31.4 mV。電池系のL3配線は1.2 mmへ広げました。MCP73831の最悪条件例は5.25 V入力・3.0 V電池・110 mAで約0.248 W、θJA=230℃/Wを仮定した接合温度約107℃です。温度・効率・銅厚等の仮定を含み、組立基板の実測値ではありません。[電源計算](validation/electrical-audit.json)

Samsungの公開DCバイアス曲線を確認しました。初期公差−20%、温度−15%、経年余裕−10%を掛けたスクリーニングで、5.25 V時は約6.27 µF、3.3 V時の2個合計は約18.23 µFとなり、入力4.7 µF・出力15 µFの設計目標を上回ります。これはメーカー典型曲線と仮定の組合せであり、全条件の保証値ではありません。[容量確認](validation/capacitor-screen.json)、[Samsung](https://product.samsungsem.com/mlcc/CL21A226MAQNNN.do)

製造前に残る確認は、部品調達と代替品の再評価、両面実装の向きと極性、JLCPCBの実スタックアップとUSBインピーダンスです。公称容量から実効容量を保証していません。U1/U2のサーマルビアには平坦な充填・キャップ仕上げが必要です。実機では、カード挿抜、筐体・シールドの高さ、USB通信、無線とSD同時動作、電源切替、充電終了、負荷・温度・USB波形を確認してください。

v0.5のアップロード済みBOM/CPL・Gerberをv0.6へ混用しないでください。v0.6は両面実装の見積もり用設計です。注文・決済はしていません。
