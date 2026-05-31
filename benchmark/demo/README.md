# デモ用データ（knowledge_distillation を実際に回す）

ガバナンス判定（既存FAQ更新候補・矛盾可能性）が**狙って発火する**よう用意した合成データです。
実顧客データではありません。

## ファイル

| ファイル | 役割 |
|---|---|
| `knowledge_distillation_start_inquiries.csv` | **入力**：問い合わせ履歴（10件）。VPN/ゲストWi-Fi/経費/パスワード等の最新対応 |
| `knowledge_distillation_start_existing_faq.csv` | 旧FAQ（参考・CSV版） |
| `approved_knowledge.demo_baseline.json` | **比較元（Before）**：旧FAQ5件を approved_knowledge.json 形式にしたもの（`demo-*` ID・旧回答） |

> ポイント：入力ログは**新手順**、比較元は**旧FAQ**。差があるから「更新候補／矛盾可能性」が出ます。
> 例）VPN: 旧「再起動」→ 新「最新版へ更新」＝更新候補／ゲストWi-Fi: 旧「使用不可」→ 新「利用可」＝矛盾可能性。

## 実行手順（Streamlit UI で実際に回す）

1. **比較元を Before に向ける**（稼働中の `data/approved_knowledge.json` は触らない）
   - ⚠️ アプリは起動時に作業ディレクトリを `knowledge_distillation/` に変更するため、
     **APPROVED_KNOWLEDGE_PATH は必ず「絶対パス」**で指定してください（相対パスは効きません）。
   ```bat
   set APPROVED_KNOWLEDGE_PATH=C:\Users\yukai\Desktop\Knowledge_Governance_Layer\Knowledge_Governance_Layer-git\benchmark\demo\approved_knowledge.demo_baseline.json
   ```
   （PowerShell: `$env:APPROVED_KNOWLEDGE_PATH="C:\Users\yukai\Desktop\Knowledge_Governance_Layer\Knowledge_Governance_Layer-git\benchmark\demo\approved_knowledge.demo_baseline.json"`）

2. **アプリ起動**
   ```bat
   open_knowledge_distillation.bat
   ```
   （または `python -m streamlit run knowledge_distillation/app.py`）

3. **問い合わせ履歴CSVをアップロード**
   - 「1️⃣ 問い合わせ履歴CSV」に `knowledge_distillation_start_inquiries.csv`

4. **比較対象を確認**
   - 「2️⃣ 承認済みKnowledge（比較対象）」に上記ベースラインの**5件**が読み込まれていることを確認
   - （しきい値スライダー「Phase 3-2」は既定 **0.70**）

5. **実行 → 結果Excelを確認**
   - Sheet1「最終ナレッジ候補一覧」で、VPN系が **推奨アクション=既存FAQ更新（既存FAQ更新候補）**、
     ゲストWi-Fiが **矛盾可能性**、`既存FAQ_ID` に `demo-vpn-001` 等が入ることを確認

6. **レビューで「採用」→ approved_knowledge 出力**
   - upsert マージで `既存FAQ_ID` を持つ更新候補は**旧FAQを上書き**、新規は追加（重複なし）

## 注意

- 既存FAQ照合は **質問＋回答** を結合した埋め込み類似度で行います（しきい値 0.70）。
- 類似度の実数は **Azure 埋め込み（text-embedding-3-large）** での実行で確定します。
  狙い通り発火しない場合は、Before の文言をログに寄せる／しきい値を微調整してください。
- Codex の台本式デモ（`prepare_live_demo.py` / `approved_knowledge_before.json` / `_after.json`）は
  VPN中心の事前生成Excelデモで、本READMEの「実際に回す」手順とは別物です。
