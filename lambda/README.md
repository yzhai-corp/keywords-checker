# AWS Lambda デプロイメント

AWS Lambdaにバックエンドをデプロイするための構成ファイル群です。

## ディレクトリ構成

```
lambda/
├── lambda1/                    # Lambda1: Excel処理とオーケストレーション
│   ├── lambda_function.py      # Lambda1のメインコード
│   └── requirements.txt        # Lambda1の依存関係
├── lambda2/                    # Lambda2: LLM API呼び出し
│   ├── lambda_function.py      # Lambda2のメインコード
│   └── requirements.txt        # Lambda2の依存関係
├── build/                      # ビルド成果物（.gitignoreに含む）
│   ├── skills-layer.zip        # Lambda Layer (SKILLファイル)
│   ├── lambda1.zip             # Lambda1デプロイパッケージ
│   └── lambda2.zip             # Lambda2デプロイパッケージ
├── build.sh                    # ビルドスクリプト
└── DEPLOY.md                   # デプロイ手順書
```

## アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│  S3 Bucket                                      │
│  askul-sandbox-01-regulation-test-bucket        │
│                                                 │
│  input/sample.xlsx                              │
│  output/result_20260203.xlsx                    │
└──────────────┬──────────────────────────────────┘
               │
               ├─ S3 Get Object
               │
┌──────────────▼──────────────────────────────────┐
│  Lambda1: keywords-checker-lambda1              │
│  - Excelファイルを読み込み                          │
│  - 行ごとに処理してLambda2を呼び出し                   │
│  - 結果を統合してExcelに書き戻し                       │
│  - S3にアップロード                                │
│                                                 │
│  Memory: 2048 MB                                │
│  Timeout: 15分                                  │
└────────┬────────────────────────────────────────┘
         │
         ├─ Lambda Invoke (並列)
         │
┌────────▼────────────────────────────────────────┐
│  Lambda2: keywords-checker-lambda2 (×複数)      │
│  - キーワード検索                                   │
│  - referenceファイル読み込み                        │
│  - LLM APIにリクエスト                             │
│  - 結果を返す                                     │
│                                                 │
│  Memory: 1024 MB                                │
│  Timeout: 2分                                   │
│  Reserved Concurrency: 100                      │
└─────────────────────────────────────────────────┘
         │
         └─ LiteLLM API
            https://askul-gpt.askul-it.com/v1
```

## クイックスタート

### 1. ビルド

```bash
cd lambda
./build.sh
```

ビルドスクリプトは以下を実行します：
- Lambda Layer (skills-layer.zip) の作成
- Lambda1 (lambda1.zip) のパッケージング
- Lambda2 (lambda2.zip) のパッケージング

### 2. デプロイ

詳細な手順は [DEPLOY.md](./DEPLOY.md) を参照してください。

### 3. テスト

Lambda1のテストイベント：

```json
{
  "input_file": "input/sample.xlsx",
  "output_file": "output/result.xlsx"
}
```

## 主な機能

### Lambda1 (Orchestrator)

- S3からExcelファイルをダウンロード
- ヘッダー行の自動検出（0-5行目をスキャン）
- 商品情報の抽出（7項目）
- チェック対象データの抽出（8項目）
- Lambda2への並列呼び出し
- 結果の統合とExcel形式への変換
- S3へのアップロード
- openpyxlによるスタイル保持（背景色、フォント等）

### Lambda2 (Worker)

- キーワードマッチング（200+キーワード）
- referenceファイルの読み込み
- LLM APIへのリクエスト（LiteLLM経由）
- 結果のパース（OK/NG/対象キーワード存在しない）

## 環境変数

### Lambda1

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `BUCKET_NAME` | S3バケット名 | `askul-sandbox-01-regulation-test-bucket` |
| `LAMBDA2_FUNCTION_NAME` | Lambda2の関数名 | `keywords-checker-lambda2` |

### Lambda2

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `LITELLM_API_BASE` | LLM APIのエンドポイント | `https://askul-gpt.askul-it.com/v1` |
| `LITELLM_MODEL` | 使用するモデル | `gpt-5-mini` |
| `OPENAI_API_KEY` | API認証キー | (required) |

## パフォーマンス設定

### Lambda2の同時実行数

最大10,000件のデータを15分以内で処理する場合：

- 1件あたり2分かかると仮定
- 15分 = 900秒
- 必要な並列数 = 10,000 × 2分 / 15分 ≈ 1,333

→ Reserved Concurrency: **100** (まずは控えめに設定、必要に応じて増やす)

### メモリとタイムアウト

| Lambda | Memory | Timeout | 理由 |
|--------|--------|---------|------|
| Lambda1 | 2048 MB | 15分 | Excel処理とオーケストレーション |
| Lambda2 | 1024 MB | 2分 | LLM API呼び出し |

## コスト見積もり

### Lambda1
- リクエスト数: 月100回
- 実行時間: 15分/回
- メモリ: 2048 MB

### Lambda2
- リクエスト数: 月10,000回 × 100並列 = 1,000,000回
- 実行時間: 2分/回
- メモリ: 1024 MB

※ 実際のコストはAWS料金計算ツールで確認してください。

## トラブルシューティング

### メモリ不足

```
Error: Runtime exited with error: signal: killed Runtime.ExitError
```

→ Lambda1/Lambda2のメモリを増やす

### タイムアウト

```
Task timed out after 120.00 seconds
```

→ Lambda2のタイムアウトを増やす、または同時実行数を増やす

### Lambda2が見つからない

```
ResourceNotFoundException: Function not found
```

→ `LAMBDA2_FUNCTION_NAME` 環境変数を確認

### S3アクセスエラー

```
AccessDenied: Access Denied
```

→ Lambda1のIAMロールに S3 アクセス権限を付与

## 監視

CloudWatch Logsで確認：

```bash
# Lambda1
aws logs tail /aws/lambda/keywords-checker-lambda1 --follow

# Lambda2
aws logs tail /aws/lambda/keywords-checker-lambda2 --follow
```

## ローカル開発

Lambda関数をローカルでテストする場合：

```bash
# Lambda2のテスト
cd lambda/lambda2
python -c "
from lambda_function import lambda_handler
event = {
    'row_index': 0,
    'product_message': '*商品名: テスト\n変更後_キャッチコピーBtoB: 健康促進'
}
result = lambda_handler(event, None)
print(result)
"
```

## 更新履歴

- 2026-02-03: 初版作成
