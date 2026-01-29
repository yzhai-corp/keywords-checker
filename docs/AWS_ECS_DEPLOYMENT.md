# AWS ECS Deployment Guide for Keywords Checker

## 前提条件

- AWS CLI がインストールされている
- Docker がインストールされている
- AWS アカウントと適切な権限がある
- ECR リポジトリが作成されている

## デプロイ手順

### 1. AWS リソースの準備

#### 1.1 ECR リポジトリの作成

```bash
# ECRリポジトリを作成
aws ecr create-repository \
    --repository-name keywords-checker \
    --region ap-northeast-1

# レスポンスから repositoryUri を記録する
```

#### 1.2 Secrets Manager でAPIキーを設定

```bash
# APIキーをSecrets Managerに保存
aws secretsmanager create-secret \
    --name keywords-checker/api-key \
    --description "LiteLLM API Key for Keywords Checker" \
    --secret-string '{"OPENAI_API_KEY":"your-api-key-here"}' \
    --region ap-northeast-1
```

#### 1.3 CloudWatch Logs グループの作成

```bash
aws logs create-log-group \
    --log-group-name /ecs/keywords-checker \
    --region ap-northeast-1
```

#### 1.4 IAM ロールの作成

**ECS Task Execution Role** (ecsTaskExecutionRole):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. ローカルビルドとテスト

#### 2.1 Docker イメージのビルド

```bash
# プロジェクトルートで実行
docker build -t keywords-checker:latest .
```

#### 2.2 ローカルでテスト

```bash
# docker-composeで起動
docker-compose up -d

# ヘルスチェック
curl http://localhost:5001/api/health

# ログ確認
docker-compose logs -f

# 停止
docker-compose down
```

### 3. ECRへのプッシュ

```bash
# 環境変数を設定
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=ap-northeast-1
export ECR_REPOSITORY=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/keywords-checker

# ECRにログイン
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${ECR_REPOSITORY}

# イメージにタグを付ける
docker tag keywords-checker:latest ${ECR_REPOSITORY}:latest

# ECRにプッシュ
docker push ${ECR_REPOSITORY}:latest
```

### 4. ECS クラスターの作成

```bash
# Fargate クラスターを作成
aws ecs create-cluster \
    --cluster-name keywords-checker-cluster \
    --region ap-northeast-1
```

### 5. タスク定義の登録

```bash
# task-definition.json を編集して実際のAWS_ACCOUNT_IDとAWS_REGIONに置き換える
sed -i '' 's/{AWS_ACCOUNT_ID}/123456789012/g' task-definition.json
sed -i '' 's/{AWS_REGION}/ap-northeast-1/g' task-definition.json

# タスク定義を登録
aws ecs register-task-definition \
    --cli-input-json file://task-definition.json \
    --region ap-northeast-1
```

### 6. Application Load Balancer (ALB) の設定

#### 6.1 セキュリティグループの作成

```bash
# ALB用セキュリティグループ
aws ec2 create-security-group \
    --group-name keywords-checker-alb-sg \
    --description "Security group for Keywords Checker ALB" \
    --vpc-id vpc-xxxxxx

# HTTP/HTTPSアクセスを許可
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxx \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

# ECS Task用セキュリティグループ
aws ec2 create-security-group \
    --group-name keywords-checker-ecs-sg \
    --description "Security group for Keywords Checker ECS Tasks" \
    --vpc-id vpc-xxxxxx

# ALBからのアクセスを許可
aws ec2 authorize-security-group-ingress \
    --group-id sg-yyyyyy \
    --protocol tcp \
    --port 5001 \
    --source-group sg-xxxxxx
```

#### 6.2 ALBの作成

```bash
# ターゲットグループを作成
aws elbv2 create-target-group \
    --name keywords-checker-tg \
    --protocol HTTP \
    --port 5001 \
    --vpc-id vpc-xxxxxx \
    --target-type ip \
    --health-check-path /api/health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3

# ALBを作成
aws elbv2 create-load-balancer \
    --name keywords-checker-alb \
    --subnets subnet-xxxxxx subnet-yyyyyy \
    --security-groups sg-xxxxxx

# リスナーを作成
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:... \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

### 7. ECS サービスの作成

```bash
aws ecs create-service \
    --cluster keywords-checker-cluster \
    --service-name keywords-checker-service \
    --task-definition keywords-checker-task \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxx,subnet-yyyyyy],securityGroups=[sg-yyyyyy],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=keywords-checker,containerPort=5001" \
    --region ap-northeast-1
```

### 8. CI/CD パイプラインの設定 (AWS CodePipeline + CodeBuild)

#### 8.1 CodeBuild プロジェクトの作成

```bash
aws codebuild create-project \
    --name keywords-checker-build \
    --source type=GITHUB,location=https://github.com/your-org/keywords-checker.git \
    --artifacts type=NO_ARTIFACTS \
    --environment type=LINUX_CONTAINER,image=aws/codebuild/standard:7.0,computeType=BUILD_GENERAL1_SMALL,privilegedMode=true \
    --service-role arn:aws:iam::${AWS_ACCOUNT_ID}:role/CodeBuildServiceRole \
    --region ap-northeast-1
```

#### 8.2 環境変数の設定

CodeBuildプロジェクトに以下の環境変数を設定：

```bash
AWS_ACCOUNT_ID=123456789012
AWS_DEFAULT_REGION=ap-northeast-1
IMAGE_REPO_NAME=keywords-checker
```

### 9. デプロイの確認

```bash
# サービスステータス確認
aws ecs describe-services \
    --cluster keywords-checker-cluster \
    --services keywords-checker-service

# タスクの確認
aws ecs list-tasks \
    --cluster keywords-checker-cluster \
    --service-name keywords-checker-service

# ログの確認
aws logs tail /ecs/keywords-checker --follow
```

### 10. アプリケーションへのアクセス

```bash
# ALBのDNS名を取得
aws elbv2 describe-load-balancers \
    --names keywords-checker-alb \
    --query 'LoadBalancers[0].DNSName' \
    --output text

# ブラウザでアクセス
# http://<ALB-DNS-NAME>/
```

## リソース構成

```
┌─────────────────────────────────────────────┐
│          Application Load Balancer          │
│         (keywords-checker-alb)              │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────┐
│  ECS Task   │  │  ECS Task   │
│  (Fargate)  │  │  (Fargate)  │
│  Port: 5001 │  │  Port: 5001 │
└─────────────┘  └─────────────┘
       │                │
       └────────┬────────┘
                │
        ┌───────▼────────┐
        │  Target Group  │
        │ Health: /api/  │
        │      health    │
        └────────────────┘
```

## コスト試算 (東京リージョン)

- **Fargate (1vCPU, 2GB RAM)**: $0.05/時間 × 2タスク = $0.10/時間
- **ALB**: $0.0243/時間
- **ECR ストレージ**: ~$0.10/GB/月
- **CloudWatch Logs**: ~$0.50/GB
- **データ転送**: 実際の使用量による

**月額推定**: 約 $80-100 (24時間稼働、軽度使用の場合)

## スケーリング設定

```bash
# Auto Scalingターゲットを登録
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/keywords-checker-cluster/keywords-checker-service \
    --min-capacity 2 \
    --max-capacity 10

# スケーリングポリシーを作成
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/keywords-checker-cluster/keywords-checker-service \
    --policy-name keywords-checker-cpu-scaling \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

**scaling-policy.json**:
```json
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
```

## トラブルシューティング

### タスクが起動しない

```bash
# タスクの詳細を確認
aws ecs describe-tasks \
    --cluster keywords-checker-cluster \
    --tasks <task-id>

# stopped-reasonを確認
```

### ヘルスチェックが失敗する

```bash
# コンテナログを確認
aws logs tail /ecs/keywords-checker --follow

# タスク内からヘルスチェックを手動実行
aws ecs execute-command \
    --cluster keywords-checker-cluster \
    --task <task-id> \
    --container keywords-checker \
    --interactive \
    --command "/bin/bash"
```

## セキュリティベストプラクティス

1. **VPC内にプライベートサブネットを使用**
2. **ALBのみパブリックに公開**
3. **Secrets Managerで機密情報を管理**
4. **IAMロールは最小権限の原則に従う**
5. **セキュリティグループで必要最小限のポートのみ開放**
6. **CloudWatch Logsで監査ログを記録**
7. **定期的なイメージスキャン (ECR Image Scanning)**

## メンテナンス

### イメージの更新

```bash
# 新しいイメージをビルド&プッシュ
docker build -t keywords-checker:latest .
docker tag keywords-checker:latest ${ECR_REPOSITORY}:latest
docker push ${ECR_REPOSITORY}:latest

# サービスを強制的に新しいデプロイ
aws ecs update-service \
    --cluster keywords-checker-cluster \
    --service keywords-checker-service \
    --force-new-deployment
```

### ログのローテーション

CloudWatch Logsで保持期間を設定：

```bash
aws logs put-retention-policy \
    --log-group-name /ecs/keywords-checker \
    --retention-in-days 30
```
