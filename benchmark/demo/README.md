# デモ用ベースライン（Before/After）

ガバナンス判定（既存FAQ更新候補・矛盾可能性）が**狙って発火する**ように用意した、
**合成の「Before」承認済みナレッジ**です。実顧客データではありません。

- `approved_knowledge.before.json` … デモ開始時点の**旧FAQ**（VPN再起動・ゲストWi-Fi利用不可・パスワード電話依頼・プリンタWi-Fi確認・経費は紙申請）

## なぜ必要か

既存FAQ照合（Phase 3-2）は、**approved_knowledge.json（＝今の承認済みナレッジ）**を
比較元にします。比較元に「旧FAQ」が入っていないと、新しい問い合わせログは
すべて「新規FAQ作成」になり、**更新候補/矛盾の検知が発火しません**。
この Before を比較元に据えると、ログ（最新の手順）と旧FAQが食い違うため、
`既存FAQ更新候補` / `既存FAQ矛盾可能性` が出ます。

## デモ手順（Before → After）

1. **Before を比較元に設定**（稼働中の `data/approved_knowledge.json` は触らずに切替）
   ```bash
   # 環境変数で比較元を Before に向ける（distillation 実行時）
   set APPROVED_KNOWLEDGE_PATH=benchmark/demo/approved_knowledge.before.json   # Windows
   # export APPROVED_KNOWLEDGE_PATH=benchmark/demo/approved_knowledge.before.json  # macOS/Linux
   ```
   ※ もしくはこのファイルを `data/approved_knowledge.json` にコピーする。

2. **distillation を実行**（問い合わせログを投入）
   - VPN/ゲストWi-Fi/パスワード/プリンタ/経費の候補が、旧FAQと照合され
     `既存FAQ更新候補`（推奨アクション=既存FAQ更新）や
     `既存FAQ矛盾可能性`（ゲストWi-Fi: 利用不可→利用可）として出る

3. **レビューで「採用」→ approved_knowledge を出力**
   - upsert マージにより、`既存FAQ_ID` を持つ更新候補は**旧FAQを上書き**、新規は追加

4. **After を serving で確認**
   - 出力された approved_knowledge.json を `data/approved_knowledge.json` に置き、
     serving を起動 → 旧手順だった質問が**最新の回答**で返る

## 補足（しきい値・照合方式）

- 既存FAQ照合は **質問＋回答** を結合して埋め込み類似度で照合します
- 更新候補のしきい値は **0.70**（同テーマ・別表現の取りこぼしを減らすため）
- 最終的な類似度の実数は **Azure 埋め込みでの実行**で決まります。狙いどおり発火しない
  場合は、Before の文言をログに寄せる／しきい値を微調整してください
