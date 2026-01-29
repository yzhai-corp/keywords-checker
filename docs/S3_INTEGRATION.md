# S3統合ガイド - Keywords Checker

## 概要

2つのS3バケットを使用して、Excelファイルの処理とSkills定義・参照ファイルの管理を分離します。
- **Excel Bucket**: Excelファイルの入出力（キャッシュなし）
- **Skills Bucket**: Skills定義・参照ファイル（Redisキャッシュあり）

## 🏗️ アーキテクチャ

```
┌───────────────────────────────────────────────────┐
│         S3 Excel Bucket (キャッシュなし)         │
│       keywords-checker-excel                      │
├───────────────────────────────────────────────────┤
│  input/                                           │
│  ├── product_list.xlsx       ← アップロード       │
│  └── product_list_2.xlsx                          │
│                                                    │
│  output/                                          │
│  ├── product_list_checked_20260127_123456.xlsx    │
│  └── product_list_2_checked_20260127_134500.xlsx  │
└───────────────────────────────────────────────────┘
           ↑                           ↑
           │                           │
    ┌──────┴────────┐         ┌────────┴────────┐
    │ EventBridge   │         │   ECS Service   │
    │   (自動)      │         │   (処理実行)    │
    └───────────────┘         └─────────────────┘
           ↓
    ┌──────────────┐
    │    Lambda    │
    │  (トリガー)  │
    └──────────────┘
           ↓
    API呼び出し: POST /api/check-excel-s3

┌───────────────────────────────────────────────────┐
│      S3 Skills Bucket (Redisキャッシュあり)      │
│       keywords-checker-skills                     │
├───────────────────────────────────────────────────┤
│  SKILL.md                    ← スキル定義         │
│  references/                                      │
│  ├── keyword1.md                                  │
│  ├── keyword2.md                                  │
│  └── ...  (200+ファイル)                         │
└───────────────────────────────────────────────────┘
           ↑
           │
    ┌──────┴────────┐
    │ ElastiCache   │
    │    Redis      │
    │  (24h TTL)    │
    └───────────────┘
           ↑
           │
    ┌──────┴────────┐
    │  ECS Service  │
    │ (Skills取得)  │
    └───────────────┘
```

## 📋 前提条件

### 1. S3バケットの作成

```bash
# Excel用バケットを作成
aws s3 mb s3://keywords-checker-excel --region ap-northeast-1

# Skills用バケットを作成
aws s3 mb s3://keywords-checker-skills --region ap-northeast-1

# Excelバケットのディレクトリ構造を作成
aws s3api put-object --bucket keywords-checker-excel --key input/
aws s3api put-object --bucket keywords-checker-excel --key output/
```

### 2. IAMロールの設定

**ECS Task Role** に以下のポリシーを追加：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::keywords-checker-excel",
        "arn:aws:s3:::keywords-checker-excel/input/*",
        "arn:aws:s3:::keywords-checker-skills",
        "arn:aws:s3:::keywords-checker-skills/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::keywords-checker-excel/output/*"
      ]
    }
  ]
}
```

### 3. 環境変数の設定

```bash
# .envファイルまたはECS Task Definitionで設定
EXCEL_BUCKET_NAME=keywords-checker-excel
SKILLS_BUCKET_NAME=keywords-checker-skills
REDIS_HOST=your-redis-cluster-endpoint.cache.amazonaws.com
REDIS_PORT=6379
```

### 4. ElastiCache (Redis) の設定

#### 4.1 Redis クラスターの作成

CloudFormationテンプレートで自動作成されますが、手動作成する場合:

```bash
# Subnet Groupの作成
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name keywords-checker-cache-subnet \
  --cache-subnet-group-description "Subnet group for Keywords Checker Redis" \
  --subnet-ids subnet-xxxxx subnet-yyyyy

# Security Groupの作成
aws ec2 create-security-group \
  --group-name keywords-checker-redis-sg \
  --description "Security group for Redis cluster" \
  --vpc-id vpc-xxxxx

# Security Groupルールの追加（ECSからのアクセスを許可）
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 6379 \
  --source-group sg-yyyyy  # ECS Security Group ID

# Redis クラスターの作成
aws elasticache create-cache-cluster \
  --cache-cluster-id keywords-checker-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --cache-subnet-group-name keywords-checker-cache-subnet \
  --security-group-ids sg-xxxxx \
  --tags Key=Name,Value=keywords-checker-redis
```

#### 4.2 Redis エンドポイントの取得

```bash
# クラスター情報を取得
aws elasticache describe-cache-clusters \
  --cache-cluster-id keywords-checker-redis \
  --show-cache-node-info

# エンドポイントを環境変数に設定
REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id keywords-checker-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
  --output text)

echo "Redis Endpoint: $REDIS_ENDPOINT"
```

#### 4.3 キャッシュ動作の仕組み

```
1. ECS起動時:
   ├── Redisに接続テスト
   ├── 接続成功 → キャッシュ有効化
   └── 接続失敗 → キャッシュ無効化（S3直接アクセスにフォールバック）

2. Skillsファイル取得時:
   ├── Redisキャッシュをチェック
   ├── キャッシュHIT → Redisから取得 (50ms)
   └── キャッシュMISS → S3から取得 → Redisにキャッシュ (500ms)

3. キャッシュ有効期限:
   ├── TTL: 24時間
   ├── 自動削除: TTL経過後
   └── 手動削除: API経由 or Redis CLI
```

#### 4.4 キャッシュのメリット

| 項目 | S3直接アクセス | Redisキャッシュ | 改善率 |
|------|---------------|----------------|--------|
| **レスポンスタイム** | 500ms | 50ms | **90%削減** |
| **S3 GETリクエスト** | 1,000回/日 | 50回/日 | **95%削減** |
| **200+ファイル読込** | 毎回S3アクセス | 24時間キャッシュ | **コスト削減** |
| **同時アクセス負荷** | S3に集中 | Redis分散 | **高速化** |

## 🚀 使用方法

### 方法1: 手動APIコール

最新のExcelファイルを処理：

```bash
curl -X POST http://your-alb-url.com/api/check-excel-s3 \
  -H "Content-Type: application/json" \
  -d '{
    "skill_name": "商品コピーチェック"
  }'
```

特定のファイルを処理：

```bash
curl -X POST http://your-alb-url.com/api/check-excel-s3 \
  -H "Content-Type: application/json" \
  -d '{
    "skill_name": "商品コピーチェック",
    "file_key": "input/specific_file.xlsx"
  }'
```

レスポンス例：

```json
{
  "status": "success",
  "input_file": "input/product_list.xlsx",
  "output_file": "output/product_list_checked_20260127_123456.xlsx",
  "rows_processed": 100,
  "download_url": "https://keywords-checker-files.s3.ap-northeast-1.amazonaws.com/...",
  "bucket": "keywords-checker-files"
}
```

### 方法2: Lambda + EventBridge (自動)

#### 2.1 Lambda関数の作成

```bash
# Lambda関数を作成
aws lambda create-function \
  --function-name keywords-checker-s3-processor \
  --runtime python3.11 \
  --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda/s3_processor_lambda.zip \
  --timeout 600 \
  --memory-size 256 \
  --environment Variables="{API_ENDPOINT=http://your-alb-url.com}"
```

#### 2.2 EventBridge Rule の作成

```bash
# S3にファイルがアップロードされたらLambdaをトリガー
aws events put-rule \
  --name keywords-checker-s3-upload \
  --event-pattern '{
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {
        "name": ["keywords-checker-files"]
      },
      "object": {
        "key": [{"prefix": "input/"}]
      }
    }
  }'

# LambdaをターゲットとしてEventBridge Ruleに追加
aws events put-targets \
  --rule keywords-checker-s3-upload \
  --targets "Id"="1","Arn"="arn:aws:lambda:ap-northeast-1:${AWS_ACCOUNT_ID}:function:keywords-checker-s3-processor"

# LambdaにEventBridgeからの呼び出しを許可
aws lambda add-permission \
  --function-name keywords-checker-s3-processor \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:ap-northeast-1:${AWS_ACCOUNT_ID}:rule/keywords-checker-s3-upload
```

#### 2.3 S3イベント通知の有効化

```bash
# EventBridgeへの通知を有効化
aws s3api put-bucket-notification-configuration \
  --bucket keywords-checker-files \
  --notification-configuration '{
    "EventBridgeConfiguration": {}
  }'
```

## 🔄 ワークフロー

### 自動処理フロー

```
1. ユーザーがS3にExcelファイルをアップロード
   ↓
2. S3 → EventBridge にイベント送信
   ↓
3. EventBridge → Lambda関数をトリガー
   ↓
4. Lambda → ECS API (/api/check-excel-s3) を呼び出し
   ↓
5. ECS:
   - S3から最新ファイルを取得
   - 商品コピーをチェック
   - 結果をS3にアップロード
   ↓
6. ユーザーがS3から結果ファイルをダウンロード
```

### 手動処理フロー

```
1. API呼び出し: POST /api/check-excel-s3
   ↓
2. ECS:
   - S3から最新ファイル取得
   - 処理実行
   - 結果をS3に保存
   ↓
3. レスポンスでダウンロードURLを取得
   ↓
4. presigned URLから結果をダウンロード
```

## 📁 S3ディレクトリ構造

```
keywords-checker-files/
├── input/
│   ├── product_list_20260127.xlsx
│   ├── product_list_20260126.xlsx
│   └── ...
│
└── output/
    ├── product_list_20260127_checked_123456.xlsx
    ├── product_list_20260126_checked_234567.xlsx
    └── ...
```

## 🔐 セキュリティ

### S3バケットポリシー

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedObjectUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::keywords-checker-files/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    },
    {
      "Sid": "DenyInsecureConnections",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::keywords-checker-files/*",
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

### バケット暗号化

```bash
aws s3api put-bucket-encryption \
  --bucket keywords-checker-files \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### ライフサイクルポリシー

```bash
# 古いファイルを自動削除
aws s3api put-bucket-lifecycle-configuration \
  --bucket keywords-checker-files \
  --lifecycle-configuration '{
    "Rules": [
      {
        "Id": "DeleteOldOutputFiles",
        "Status": "Enabled",
        "Prefix": "output/",
        "Expiration": {
          "Days": 30
        }
      },
      {
        "Id": "DeleteOldInputFiles",
        "Status": "Enabled",
        "Prefix": "input/",
        "Expiration": {
          "Days": 7
        }
      }
    ]
  }'
```

### ElastiCache セキュリティ設定

#### ネットワーク隔離

```bash
# Private Subnet内に配置
- Redis クラスターはPrivate Subnetに配置
- インターネットから直接アクセス不可
- ECSタスクからのみアクセス可能

# Security Group設定
aws ec2 authorize-security-group-ingress \
  --group-id sg-redis-xxxxx \
  --protocol tcp \
  --port 6379 \
  --source-group sg-ecs-yyyyy  # ECS Security Groupのみ許可
```

#### 暗号化

```bash
# At-Rest暗号化（作成時に設定）
aws elasticache create-cache-cluster \
  --cache-cluster-id keywords-checker-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --at-rest-encryption-enabled \
  --auth-token "your-strong-password"  # オプション

# In-Transit暗号化
aws elasticache create-cache-cluster \
  --cache-cluster-id keywords-checker-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --transit-encryption-enabled
```

#### アクセス制御

```yaml
ElastiCacheセキュリティベストプラクティス:
  ✅ Private Subnet配置
  ✅ Security Group制限（ECSのみ許可）
  ✅ At-Rest暗号化有効化
  ✅ In-Transit暗号化有効化（TLS）
  ✅ AUTH認証トークン設定（オプション）
  ✅ VPC Peering経由のアクセス制限
  ✅ CloudWatch監視有効化
```
      },
      {
        "Id": "DeleteOldInputFiles",
        "Status": "Enabled",
        "Prefix": "input/",
        "Expiration": {
          "Days": 7
        }
      }
    ]
  }'
```

## 📊 モニタリング

### CloudWatch Logs

```bash
# Lambda実行ログ
aws logs tail /aws/lambda/keywords-checker-s3-processor --follow

# ECS処理ログ
aws logs tail /ecs/keywords-checker --follow
```

### CloudWatch Metrics

**Lambda:**
- `AWS/Lambda/Invocations` - Lambda実行回数
- `AWS/Lambda/Errors` - Lambda エラー数
- `AWS/Lambda/Duration` - Lambda実行時間

**S3:**
- `AWS/S3/NumberOfObjects` - S3オブジェクト数
- `AWS/S3/BucketSizeBytes` - バケットサイズ

**ElastiCache:**
- `AWS/ElastiCache/CPUUtilization` - CPU使用率
- `AWS/ElastiCache/NetworkBytesIn` - ネットワーク受信
- `AWS/ElastiCache/NetworkBytesOut` - ネットワーク送信
- `AWS/ElastiCache/CacheHits` - キャッシュヒット数
- `AWS/ElastiCache/CacheMisses` - キャッシュミス数
- `AWS/ElastiCache/CurrConnections` - 現在の接続数
- `AWS/ElastiCache/Evictions` - 削除されたアイテム数

### Redis キャッシュ統計の確認

```bash
# アプリケーションAPIからキャッシュ統計を取得
curl http://your-alb-url.com/api/cache/stats

# レスポンス例:
{
  "enabled": true,
  "host": "keywords-checker-redis.xxxxx.cache.amazonaws.com",
  "port": 6379,
  "ttl": 86400,
  "keys": 205,
  "hits": 15420,
  "misses": 823,
  "hit_rate": "94.9%"
}
```

## 🛠️ トラブルシューティング

### Redis接続エラー

**症状**: "Redis connection failed" ログが出力される

**解決方法**:

```bash
# 1. Redisクラスターの状態確認
aws elasticache describe-cache-clusters \
  --cache-cluster-id keywords-checker-redis \
  --show-cache-node-info

# 2. Security Group設定確認
aws ec2 describe-security-groups \
  --group-ids sg-xxxxx \
  --query 'SecurityGroups[0].IpPermissions'

# 3. ECSタスクからRedisへの接続テスト
# ECSタスク内で実行:
telnet your-redis-endpoint.cache.amazonaws.com 6379

# または
redis-cli -h your-redis-endpoint.cache.amazonaws.com -p 6379 ping
# 期待される出力: PONG
```

**注意**: Redisが利用できない場合、アプリケーションは自動的にS3直接アクセスにフォールバックします。

### キャッシュが効かない

**症状**: 毎回S3からファイルを取得している

**解決方法**:

```bash
# 1. キャッシュ統計を確認
curl http://your-alb-url.com/api/cache/stats

# 2. Redis接続状態を確認
curl http://your-alb-url.com/api/health

# 3. Redisキーを手動確認
redis-cli -h your-redis-endpoint.cache.amazonaws.com -p 6379
> KEYS keywords_checker:*
> GET keywords_checker:skill:<hash>
> TTL keywords_checker:skill:<hash>

# 4. キャッシュを手動でクリア（必要に応じて）
curl -X POST http://your-alb-url.com/api/cache/flush
```

### S3アクセス権限エラー

```bash
# ECS Task Roleを確認
aws iam get-role --role-name ecsTaskRole

# ポリシーをアタッチ
aws iam attach-role-policy \
  --role-name ecsTaskRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

### Lambda タイムアウト

```bash
# タイムアウトを延長（最大15分）
aws lambda update-function-configuration \
  --function-name keywords-checker-s3-processor \
  --timeout 900
```

### ファイルが見つからない

```bash
# S3ファイル一覧を確認
aws s3 ls s3://keywords-checker-files/input/ --recursive

# APIでファイル一覧を取得
curl http://your-alb-url.com/api/s3/files
```

## 💰 コスト試算

**月間処理量**: 1,000ファイル/月

- **S3ストレージ (Excel 10GB)**: ~$0.23/月
- **S3ストレージ (Skills 50MB)**: ~$0.01/月
- **S3 PUT/GET リクエスト**: ~$0.01/月
- **Lambda実行 (256MB, 60秒/実行)**: ~$0.10/月
- **EventBridge**: 無料枠内
- **ElastiCache (cache.t3.micro)**: ~$12/月
- **データ転送**: 実使用量による

**合計**: 約 **$12.35/月** (ECSコストは別途)

### Redisキャッシュによる効果

- **Skills読み込み高速化**: S3 GET削減 95%+
- **参照ファイル200+を24時間キャッシュ**
- **レスポンスタイム改善**: 500ms → 50ms (平均)
- **S3コスト削減**: 月間数千リクエスト削減

## 🔄 アップグレードパス

### フロントエンド統合

今後、フロントエンドからS3ファイルを選択・処理できるUIを追加予定：

```javascript
// frontend/app.js に追加予定
async function listS3Files() {
  const response = await fetch(`${API_BASE_URL}/s3/files`);
  const data = await response.json();
  // ファイル一覧を表示
}

async function processS3File(fileKey) {
  const response = await fetch(`${API_BASE_URL}/check-excel-s3`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({file_key: fileKey})
  });
  // 処理結果を表示
}
```
