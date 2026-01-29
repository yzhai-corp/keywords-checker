# Keywords Checker - デプロイ構成

```
keywords-checker/
├── 📦 デプロイ方法1: CloudFormation (ワンコマンド)
│   ├── deploy-all.sh ⭐           # すべて自動デプロイ
│   └── cloudformation/
│       └── keywords-checker-stack.yaml  # インフラ定義
│
├── 📦 デプロイ方法2: 個別デプロイ
│   ├── deploy.sh                  # ECSのみ
│   ├── lambda/
│   │   └── s3_processor_lambda.py # Lambda関数
│   └── buildspec.yml              # CodeBuild (CI/CD)
│
└── 📚 ドキュメント
    ├── DEPLOYMENT_GUIDE.md        # デプロイガイド
    ├── AWS_ARCHITECTURE.md        # アーキテクチャ図
    └── S3_INTEGRATION.md          # S3統合ガイド
```

## デプロイ対象リソース

### CloudFormation 1回で作成されるもの

```
1. VPC & ネットワーク
   ├── VPC (10.0.0.0/16)
   ├── Public Subnet × 2
   ├── Private Subnet × 2
   ├── Internet Gateway
   ├── NAT Gateway
   └── Route Tables

2. S3
   └── keywords-checker-files-<account-id>
       ├── input/
       └── output/

3. ECS
   ├── Cluster
   ├── Task Definition
   ├── Service (Auto Scaling付き)
   └── CloudWatch Logs

4. Lambda
   └── s3-processor関数

5. EventBridge
   └── S3イベントルール → Lambda

6. ALB
   ├── Load Balancer
   ├── Target Group
   └── Listener

7. セキュリティ
   ├── Secrets Manager (API Key)
   ├── IAM Roles
   └── Security Groups
```

## デプロイ順序

### CloudFormation使用時
```
./deploy-all.sh 実行
    ↓
[1] ECRリポジトリ作成
    ↓
[2] Dockerビルド & プッシュ
    ↓
[3] CloudFormation Stack作成
    ├── すべてのリソースを並列作成
    └── 依存関係は自動解決
    ↓
[4] 完了 (10〜15分)
```

### 個別デプロイ時
```
[1] VPC作成 (手動)
    ↓
[2] S3バケット作成 (手動)
    ↓
[3] Secrets Manager (手動)
    ↓
[4] IAM Roles作成 (手動)
    ↓
[5] ./deploy.sh (ECS)
    ↓
[6] Lambda作成 (AWS CLI)
    ↓
[7] EventBridge設定 (AWS CLI)
    ↓
[8] 完了 (手動作業多い)
```

## 推奨デプロイ方法

| 環境 | 推奨方法 | 理由 |
|------|---------|------|
| 本番 | CloudFormation | 再現性・管理容易 |
| 開発 | CloudFormation | 素早くリセット可能 |
| 学習 | 手動 | 理解が深まる |
