# Keywords Checker - アーキテクチャ概要

## S3バケット構成

本アプリケーションは2つのS3バケットを使用します:

### 1. Excel Bucket (キャッシュなし)
**用途**: Excelファイルの入出力
- `input/`: アップロードされたExcelファイル (7日後自動削除)
- `output/`: 処理済みExcelファイル (30日後自動削除)
- **キャッシュ**: なし

### 2. Skills Bucket (Redisキャッシュあり)
**用途**: Skills定義・参照ファイルの保存
- `SKILL.md`: スキル定義ファイル
- `references/*.md`: 参照ファイル (200+ファイル)
- **キャッシュ**: ElastiCache (Redis) - 24時間TTL

## データフロー

```
1. ユーザー → Excel Bucket (input/) にアップロード
2. EventBridge → Lambda トリガー
3. Lambda → ECS API呼び出し (/api/check-excel-s3)
4. ECS:
   a. Excel Bucket から Excel取得 (キャッシュなし)
   b. Skills Bucket から Skills取得 (Redis経由でキャッシュ)
   c. LiteLLM API でチェック実行
   d. Excel Bucket (output/) に結果保存
5. ユーザー → 結果ダウンロード
```

## Redis キャッシュ戦略

- **対象**: Skills定義ファイル + 参照ファイル (200+)
- **TTL**: 24時間
- **効果**: 
  - S3 GET リクエスト 95%+ 削減
  - レスポンスタイム 500ms → 50ms (平均)
  - コスト最適化 (S3リクエスト料金削減)

## 環境変数

```bash
# Excel Bucket
EXCEL_BUCKET_NAME=keywords-checker-excel

# Skills Bucket
SKILLS_BUCKET_NAME=keywords-checker-skills

# Redis
REDIS_HOST=your-redis-cluster.cache.amazonaws.com
REDIS_PORT=6379

# LiteLLM
LITELLM_API_KEY=sk-xxxxx
LITELLM_API_BASE=https://askul-gpt.askul-it.com/v1
```

## デプロイ

```bash
# 全リソースを一括デプロイ
./deploy-all.sh
```

詳細は以下のドキュメントを参照:
- [TECH_STACK.md](TECH_STACK.md) - 技術スタック詳細
- [docs/AWS_ARCHITECTURE.md](docs/AWS_ARCHITECTURE.md) - AWS構成図
- [docs/S3_INTEGRATION.md](docs/S3_INTEGRATION.md) - S3統合ガイド
- [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) - デプロイガイド
