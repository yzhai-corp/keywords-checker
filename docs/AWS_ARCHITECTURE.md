# AWS構成図 - Keywords Checker

## 全体アーキテクチャ

```mermaid
graph TB
    subgraph "ユーザー"
        User[👤 ユーザー]
    end

    subgraph "AWS Cloud"
        subgraph "ネットワーク層"
            ALB[Application Load Balancer<br/>Port 80/443]
            Route53[Route 53<br/>DNS]
        end

        subgraph "コンピューティング層"
            subgraph "ECS Cluster"
                ECS1[ECS Task 1<br/>Flask App<br/>Port 5001]
                ECS2[ECS Task 2<br/>Flask App<br/>Port 5001]
                ECS3[ECS Task 3<br/>Flask App<br/>Port 5001]
            end
            
            Lambda[Lambda Function<br/>S3イベント処理<br/>Timeout: 600s]
        end

        subgraph "ストレージ層"
            S3Excel[S3 Excel Bucket<br/>keywords-checker-excel]
            subgraph "Excel構造"
                S3Input[📁 input/<br/>*.xlsx, *.xls]
                S3Output[📁 output/<br/>*_checked_*.xlsx]
            end
            
            S3Skills[S3 Skills Bucket<br/>keywords-checker-skills]
            subgraph "Skills構造"
                SkillFile[📄 SKILL.md]
                RefFiles[📁 references/<br/>*.md]
            end
        end

        subgraph "キャッシュ層"
            Redis[ElastiCache Redis<br/>cache.t3.micro<br/>TTL: 24h]
        end

        subgraph "監視・ログ"
            CloudWatch[CloudWatch Logs<br/>/ecs/keywords-checker<br/>/aws/lambda/...]
            EventBridge[EventBridge<br/>S3 Event Rule]
        end

        subgraph "セキュリティ"
            SecretsManager[Secrets Manager<br/>LITELLM_API_KEY]
            IAM[IAM Roles<br/>Task Role / Execution Role]
        end

        subgraph "コンテナレジストリ"
            ECR[Amazon ECR<br/>Docker Images]
        end
    end

    subgraph "外部サービス"
        LiteLLM[LiteLLM API<br/>askul-gpt.askul-it.com<br/>GPT-5-mini]
    end

    %% ユーザーフロー
    User -->|1. HTTPリクエスト| Route53
    Route53 --> ALB
    ALB -->|負荷分散| ECS1
    ALB -->|負荷分散| ECS2
    ALB -->|負荷分散| ECS3

    %% S3自動処理フロー
    User -->|2. Excelアップロード| S3Input
    S3Input -->|3. イベント通知| EventBridge
    EventBridge -->|4. Lambdaトリガー| Lambda
    Lambda -->|5. API呼び出し<br/>POST /api/check-excel-s3| ALB
    
    %% ECSとS3の直接連携
    ECS1 <-->|6a. Excelファイル取得/保存<br/>boto3 SDK| S3Excel
    ECS2 <-->|Excelファイル取得/保存| S3Excel
    ECS3 <-->|Excelファイル取得/保存| S3Excel
    
    %% SkillsファイルとRedisキャッシュ
    ECS1 <-->|6b. Skillsファイル取得| S3Skills
    ECS2 <-->|Skillsファイル取得| S3Skills
    ECS3 <-->|Skillsファイル取得| S3Skills
    S3Skills <-->|キャッシュ| Redis
    ECS1 <-->|キャッシュ読取| Redis
    ECS2 <-->|キャッシュ読取| Redis
    ECS3 <-->|キャッシュ読取| Redis
    
    %% ECSとLiteLLM
    ECS1 -->|7. LLM API呼び出し<br/>商品コピーチェック| LiteLLM
    ECS2 --> LiteLLM
    ECS3 --> LiteLLM

    %% 結果保存
    ECS1 -->|8. 結果保存| S3Output
    User -->|9. ダウンロード<br/>presigned URL| S3Output

    %% セキュリティ・認証
    ECS1 -.->|API Key取得| SecretsManager
    ECS2 -.-> SecretsManager
    ECS3 -.-> SecretsManager
    ECS1 -.->|権限| IAM
    Lambda -.->|権限| IAM

    %% ログ
    ECS1 -.->|ログ出力| CloudWatch
    ECS2 -.-> CloudWatch
    ECS3 -.-> CloudWatch
    Lambda -.->|ログ出力| CloudWatch

    %% デプロイ
    ECR -.->|イメージ取得| ECS1
    ECR -.-> ECS2
    ECR -.-> ECS3

    style User fill:#e1f5ff
    style S3 fill:#ff9900
    style ECS1 fill:#ff9900
    style ECS2 fill:#ff9900
    style ECS3 fill:#ff9900
    style Lambda fill:#ff9900
    style LiteLLM fill:#9b59b6
    style CloudWatch fill:#00a8e1
    style SecretsManager fill:#dd344c
```

## シーケンス図: S3自動処理フロー

```mermaid
sequenceDiagram
    actor User as 👤 ユーザー
    participant S3 as S3 Bucket<br/>(input/)
    participant EB as EventBridge
    participant Lambda as Lambda Function
    participant ALB as ALB
    participant ECS as ECS Task<br/>(Flask)
    participant S3Out as S3 Bucket<br/>(output/)
    participant LLM as LiteLLM API

    User->>S3: 1. Excelファイルアップロード<br/>product_list.xlsx
    Note over S3: ファイル保存完了

    S3->>EB: 2. イベント通知<br/>ObjectCreated
    Note over EB: ルールマッチング<br/>input/*.xlsx

    EB->>Lambda: 3. Lambdaトリガー<br/>S3イベント情報
    Note over Lambda: 関数起動<br/>Timeout: 600s

    Lambda->>ALB: 4. HTTP POST<br/>/api/check-excel-s3<br/>{"skill_name": "商品コピーチェック"}
    ALB->>ECS: 5. リクエスト転送

    Note over ECS: 処理開始

    ECS->>S3: 6. 最新ファイル取得<br/>list_objects_v2(Prefix='input/')
    S3-->>ECS: 7. ファイル一覧返却
    
    ECS->>S3: 8. ファイルダウンロード<br/>get_object('input/product_list.xlsx')
    S3-->>ECS: 9. ファイル内容返却

    Note over ECS: Excelファイル読み込み<br/>pandas.read_excel()

    loop 各商品行
        ECS->>LLM: 10. 商品コピーチェック<br/>{"messages": [...], "model": "gpt-5-mini"}
        LLM-->>ECS: 11. 判定結果<br/>OK/NG + 理由
        Note over ECS: 結果をExcelに書き込み
    end

    Note over ECS: タイムスタンプ生成<br/>20260127_123456

    ECS->>S3Out: 12. 結果ファイルアップロード<br/>put_object('output/product_list_checked_20260127_123456.xlsx')
    S3Out-->>ECS: 13. アップロード完了

    ECS->>S3Out: 14. presigned URL生成<br/>generate_presigned_url(ExpiresIn=3600)
    S3Out-->>ECS: 15. 一時ダウンロードURL

    ECS-->>ALB: 16. レスポンス<br/>{"status": "success", "download_url": "https://..."}
    ALB-->>Lambda: 17. レスポンス転送
    Lambda-->>EB: 18. 処理完了

    Note over User: メール通知など<br/>(別途実装が必要)
    
    User->>S3Out: 19. 結果ダウンロード<br/>presigned URL経由
    S3Out-->>User: 20. ファイルダウンロード
```

## コンポーネント詳細

### 1. ECS (Elastic Container Service)

**役割**: メインアプリケーションの実行環境

```
┌─────────────────────────────────────┐
│        ECS Fargate Task             │
├─────────────────────────────────────┤
│  Flask App (Port 5001)              │
│  ├── /api/health                    │
│  ├── /api/skills                    │
│  ├── /api/check                     │
│  ├── /api/check-excel               │
│  ├── /api/check-excel-s3  ⭐        │
│  └── /api/s3/files        ⭐        │
│                                     │
│  S3Manager (boto3)                  │
│  ├── get_latest_excel_file()        │
│  ├── upload_result_file()           │
│  └── list_input_files()             │
└─────────────────────────────────────┘
```

**リソース**:
- CPU: 1024 (1 vCPU)
- Memory: 2048 MB (2 GB)
- Auto Scaling: 1〜5タスク
- Health Check: GET /api/health

**環境変数**:
- `LITELLM_API_KEY`: Secrets Managerから取得
- `S3_BUCKET_NAME`: keywords-checker-files

### 2. Lambda Function

**役割**: S3イベントをトリガーとしてECS APIを呼び出す

```python
def lambda_handler(event, context):
    # S3イベントを検出
    # ↓
    # ECS APIを呼び出し
    response = requests.post(
        f"{API_ENDPOINT}/api/check-excel-s3",
        json={"skill_name": "商品コピーチェック"}
    )
    # ↓
    # 完了
```

**設定**:
- Runtime: Python 3.11
- Memory: 256 MB
- Timeout: 600秒 (10分)
- Environment: `API_ENDPOINT=http://your-alb-url.com`

**重要**: Lambdaはファイルを扱わない！APIを叩くだけ

### 3. S3 Bucket

**構造**:
```
keywords-checker-files/
├── input/                    ← ユーザーがアップロード
│   ├── product_list.xlsx
│   └── product_list_2.xlsx
│
└── output/                   ← ECSが保存
    ├── product_list_checked_20260127_123456.xlsx
    └── product_list_2_checked_20260127_140000.xlsx
```

**イベント通知**:
- EventBridge有効化
- ObjectCreated イベント
- Prefix: `input/`
- Suffix: `.xlsx`, `.xls`, `.xlsm`

### 4. EventBridge

**ルール設定**:
```json
{
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
}
```

**ターゲット**: Lambda Function

## データフロー比較

### パターンA: 手動処理 (Web UI経由)

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant ALB
    participant ECS
    participant LLM

    User->>Browser: Excelファイル選択
    Browser->>ALB: POST /api/check-excel<br/>(multipart/form-data)
    ALB->>ECS: ファイル転送
    ECS->>ECS: ファイル読み込み
    loop 各行
        ECS->>LLM: チェック
        LLM-->>ECS: 結果
    end
    ECS-->>Browser: 結果Excel返却
    Browser-->>User: ダウンロード
```

### パターンB: S3自動処理 (今回実装)

```mermaid
sequenceDiagram
    actor User
    participant S3
    participant EventBridge
    participant Lambda
    participant ECS
    participant LLM

    User->>S3: ファイルアップロード
    S3->>EventBridge: イベント
    EventBridge->>Lambda: トリガー
    Lambda->>ECS: API呼び出し
    ECS->>S3: ファイル取得
    S3-->>ECS: ファイル
    loop 各行
        ECS->>LLM: チェック
        LLM-->>ECS: 結果
    end
    ECS->>S3: 結果保存
    User->>S3: 結果ダウンロード
```

## ネットワーク構成

```mermaid
graph TB
    subgraph "Internet"
        User[ユーザー]
        LiteLLM[LiteLLM API]
    end

    subgraph "VPC: 10.0.0.0/16"
        subgraph "Public Subnet: 10.0.1.0/24"
            ALB[Application Load Balancer]
            NAT[NAT Gateway]
        end

        subgraph "Private Subnet 1: 10.0.10.0/24"
            ECS1[ECS Task 1]
        end

        subgraph "Private Subnet 2: 10.0.11.0/24"
            ECS2[ECS Task 2]
        end
    end

    subgraph "AWS Services (Managed)"
        S3[S3]
        Lambda[Lambda<br/>VPC外]
        EventBridge[EventBridge]
    end

    User -->|HTTPS| ALB
    ALB --> ECS1
    ALB --> ECS2
    ECS1 -->|NAT経由| LiteLLM
    ECS2 -->|NAT経由| LiteLLM
    ECS1 <-->|VPC Endpoint| S3
    ECS2 <-->|VPC Endpoint| S3
    Lambda -->|Internet| ALB
    EventBridge --> Lambda
    S3 -.->|イベント| EventBridge

    style User fill:#e1f5ff
    style ALB fill:#ff9900
    style ECS1 fill:#ff9900
    style ECS2 fill:#ff9900
    style S3 fill:#569a31
    style Lambda fill:#ff9900
```

## IAM権限構成

```mermaid
graph LR
    subgraph "ECS Task"
        Task[ECS Task]
    end

    subgraph "IAM Roles"
        TaskRole[Task Role<br/>ecsTaskRole]
        ExecRole[Execution Role<br/>ecsExecutionRole]
    end

    subgraph "AWS Services"
        S3[S3 Bucket]
        Secrets[Secrets Manager]
        Logs[CloudWatch Logs]
        ECR[ECR]
    end

    Task -->|AssumeRole| TaskRole
    Task -->|AssumeRole| ExecRole

    TaskRole -->|s3:GetObject<br/>s3:PutObject<br/>s3:ListBucket| S3
    TaskRole -->|secretsmanager:GetSecretValue| Secrets

    ExecRole -->|logs:CreateLogStream<br/>logs:PutLogEvents| Logs
    ExecRole -->|ecr:GetAuthorizationToken<br/>ecr:BatchGetImage| ECR

    style Task fill:#ff9900
    style TaskRole fill:#dd344c
    style ExecRole fill:#dd344c
```

## コスト最適化

### Lambda vs ECS直接実行

| 方式 | メリット | デメリット | コスト |
|------|---------|-----------|--------|
| **Lambda + ECS** | - イベント駆動<br/>- 自動スケール | - 2つのサービス<br/>- Lambda課金 | $0.34/月 + ECS |
| **ECS直接** | - シンプル<br/>- 管理容易 | - ポーリング必要<br/>- 常時実行 | ECSのみ |

**推奨**: Lambda使用（月間1000ファイル以下なら無料枠内）

### Auto Scaling設定

```json
{
  "TargetTrackingScaling": {
    "TargetValue": 70.0,
    "PredefinedMetric": "ECSServiceAverageCPUUtilization",
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  },
  "MinCapacity": 1,
  "MaxCapacity": 5
}
```

## モニタリングダッシュボード

```mermaid
graph TB
    subgraph "CloudWatch Dashboard"
        subgraph "ECS Metrics"
            CPU[CPU使用率]
            Memory[メモリ使用率]
            TaskCount[タスク数]
        end

        subgraph "Lambda Metrics"
            Invocations[実行回数]
            Duration[実行時間]
            Errors[エラー数]
        end

        subgraph "S3 Metrics"
            Objects[オブジェクト数]
            Requests[リクエスト数]
        end

        subgraph "Application Metrics"
            ProcessedRows[処理行数]
            NGCount[NG判定数]
            APILatency[API応答時間]
        end
    end

    subgraph "Alarms"
        CPUAlarm[CPU > 80%]
        ErrorAlarm[Error Rate > 5%]
        LatencyAlarm[Latency > 30s]
    end

    CPU -.-> CPUAlarm
    Errors -.-> ErrorAlarm
    APILatency -.-> LatencyAlarm

    CPUAlarm --> SNS[SNS Topic]
    ErrorAlarm --> SNS
    LatencyAlarm --> SNS
    SNS --> Email[📧 管理者メール]
```

## セキュリティベストプラクティス

### 1. 最小権限の原則

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
        "arn:aws:s3:::keywords-checker-files/input/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::keywords-checker-files/output/*"
      ]
    }
  ]
}
```

### 2. 暗号化

- **S3**: AES-256 (SSE-S3)
- **Secrets Manager**: KMS暗号化
- **ALB**: TLS 1.2以上
- **VPC**: VPC Endpointでプライベート通信

### 3. ネットワーク分離

- ECS: Private Subnetに配置
- ALB: Public Subnetに配置
- Lambda: VPC外 (必要に応じてVPC内も可)
- S3: VPC Endpoint経由でアクセス

## トラブルシューティング

### Lambda → ECS接続エラー

```bash
# セキュリティグループ確認
aws ec2 describe-security-groups --group-ids sg-xxxxx

# ALBリスナー確認
aws elbv2 describe-listeners --load-balancer-arn arn:aws:elasticloadbalancing:...
```

### S3アクセス拒否

```bash
# IAM Policy確認
aws iam get-role-policy --role-name ecsTaskRole --policy-name S3Access

# S3バケットポリシー確認
aws s3api get-bucket-policy --bucket keywords-checker-files
```

### Lambda タイムアウト

```bash
# Lambda設定確認
aws lambda get-function-configuration --function-name keywords-checker-s3-processor

# CloudWatch Logsで処理時間確認
aws logs tail /aws/lambda/keywords-checker-s3-processor --since 1h
```

## まとめ

### 🎯 重要ポイント

1. **Lambdaの役割**
   - ファイルを扱わない
   - ECS APIを呼び出すだけ
   - イベント駆動のトリガー

2. **ECSの役割**
   - 実際の処理を実行
   - S3から直接ファイル取得
   - LLM APIを呼び出し
   - 結果をS3に保存

3. **S3の役割**
   - ファイルストレージ
   - イベント発火
   - presigned URLで配信

### 📊 処理フロー

```
ユーザー → S3 → EventBridge → Lambda → ECS API
                                           ↓
                              ECS ←→ S3 (ファイル取得)
                               ↓
                              LLM API (チェック)
                               ↓
                              S3 (結果保存)
                               ↓
                             ユーザー (ダウンロード)
```
