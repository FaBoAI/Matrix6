# JLCPCB BOM / CPL — 部品照合用

2026-09-07、ログイン済みJLCPCBのMatrix6案件に `Matrix6-v0.5-BOM.csv` と `Matrix6-v0.5-CPL.csv` をアップロードし、「Process BOM & CPL」の処理完了を確認しました。

- BOMは22行、32部品。CPLは32行、全てTop。
- H1/H2のCPL座標は部品中心に補正済み。回転はKiCad角度の正規化までで、JLCPCBモデルとの照合は未完了です。
- 初回自動候補のC5はX5Rだったため、指定の1µF/16V/X7Rに合うSamsung CL10B105KO8NNNC（C59782）をBOMに固定して再アップロードしました。
- 自動候補に在庫不足のあった1kΩ/10kΩ抵抗を含め、抵抗4種をUNI-ROYAL 0603 / 1% / 100mW品に固定。修正後の画面では在庫不足表示が解消しました。
- 最終読取時の画面は「22 parts detected / 21 Parts confirmed / 1 parts not selected」。未選定はH1/H2のメスソケットです。これはJLCPCB側の候補照合表示で、当方の製造承認を意味しません。

## 製造承認までの残件

1. H1/H2のメーカー品番、挿入深さ・高さ、Matrix5シールドとの干渉、実装方法を決定。
2. C1/C2/C8（自動候補CL21A226MAQNNNE / C45783）のDCバイアス・温度・公差込みの実効容量を確認。BOM上のメーカー品番は未固定です。
3. C3/C4/C6/C7、赤/青LEDの自動候補について仕様・極性・寸法を確認し、BOMにメーカー品番を固定。
4. 全部品のJLCPCB配置プレビューとCADパッドを照合し、必要な回転・座標補正をCPLに反映。画面で数量0を示す行もあり、全実装対象の最終数量確認が必要です。
5. 製造条件、実装枚数（画面上は2枚）、送料込み総額を確認。

注文・支払い・部品在庫の購入は実行していません。Gerberと元CADは変更していません。

再生成は `python3 scripts/export_jlcpcb_assembly.py`。元CAD/CSVのSHA-256、参照番号の一致、ファイルハッシュは `export-validation.json` に記録しています。
