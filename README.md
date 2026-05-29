# FAQ Maker MVP

問い合わせデータを複数ソースから取り込み、FAQ候補を生成し、重複排除して、ナレッジとして保存するMVPです。  
既存の `_system/` 実装はそのまま残し、新規 `faq_maker` パッケージとして追加しています。

## セットアップ方法

1. Python 3.9以上を用意
2. 必要に応じて依存をインストール（Azure OpenAIを使う場合）

```bash
pip install openai
```

3. Azure OpenAIを使う場合は環境変数を設定

```bash
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="..."
export AZURE_OPENAI_API_KEY_EMBEDDING="..."
export AZURE_OPENAI_ENDPOINT_EMBEDDING="..."
# 任意
export AZURE_OPENAI_CHAT_MODEL="gpt-4.1"
export AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-3-large"
```

## CSVデモの実行方法

```bash
python -m faq_maker ingest --adapter csv --path sample.csv --no-openai
python -m faq_maker normalize --adapter csv --path sample.csv --out data/intermediate/normalized_snow_input.csv
python -m faq_maker export
```

出力:
- `data/intermediate/normalized_snow_input.csv`
- `data/outputs/knowledge_export.json`

## CLI

```bash
python -m faq_maker ingest --adapter csv --path sample.csv
python -m faq_maker ingest --adapter servicenow --path servicenow_export.csv
python -m faq_maker ingest --adapter graphmail --path mail.json
python -m faq_maker ingest --adapter graphmail --path mail.eml
python -m faq_maker normalize --adapter csv --path input.csv \
  --out data/intermediate/normalized_snow_input.csv \
  --question-col 問合せ内容 \
  --answer-cols 対応内容(一次),対応内容(二次) \
  --title-col コールタイトル \
  --category-col 種別
python -m faq_maker ingest --adapter csv --path sample.csv \
  --question-col 問い合わせ内容 \
  --answer-cols 一次回答,対応内容,最終回答 \
  --source-text-cols 問い合わせ内容,詳細,対応内容,備考 \
  --no-openai
python -m faq_maker export
```

## 全体アーキテクチャ

- `InputAdapter`
  - `CSVAdapter`: 列名エイリアスで共通形式へ変換
  - `ServiceNowAdapter`: ServiceNow標準列を優先しつつエイリアス許容
  - `GraphMailAdapter`: JSON/EMLから件名+本文を取り込み
- `NormalizedItem`
  - `question`, `source_text`, `answer`, `category`, `source`, `created_at`, `metadata`
- `FAQGenerator`
  - Azure OpenAIでFAQ候補生成（未設定時はローカルフォールバック）
- `EmbeddingDeduplicator`
  - Azure OpenAI Embeddingで重複排除（未設定時は文字列類似度フォールバック）
- `KnowledgeStore`
  - `SQLiteKnowledgeStore` で保存
  - `export` でJSONを出力

## 列名固定問題への対応

`faq_maker` では列名依存をAdapter層に限定しています。  
`FAQGenerator` / Deduplicator / KnowledgeStore は元CSV列名を参照せず、`NormalizedItem` のみを扱います。

## Copilot Studio連携予定

現状はSQLite + JSON/Excel出力までをMVP範囲としています。  
次段で `KnowledgeStore` 実装を差し替え、SharePoint / Dataverse を保存先として追加可能です。  
JSON出力を中間フォーマットとして、Copilot Studio Agentのナレッジ取り込みフローへ接続予定です。
