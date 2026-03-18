# Confluenceページ更新用 - ネットワーク構成セクション

以下の内容を Confluenceページ「AWSアーキテクチャ整理」に追加してください。
URL: https://askul.atlassian.net/wiki/spaces/TEC/pages/223052388/AWS

---

## ネットワーク構成

### Sandbox環境（現在）

| コンポーネント | 配置場所 | ネットワーク | アクセス元 | 備考 |
|---------------|---------|-------------|-----------|------|
| S3 Bucket | AWS グローバル | パブリック（IAM制御） | • 社内ネットワーク（豊洲）<br>• AWS Console<br>• AWS CLI | バケットポリシーで制限可能 |
| EventBridge | AWS マネージド | VPC外 | S3イベント | AWS内部通信 |
| Step Functions | AWS マネージド | VPC外 | EventBridge | AWS内部通信 |
| Lambda (Splitter) | AWS マネージド | VPC外 | Step Functions | パブリックサブネット相当 |
| Lambda (Processor) | AWS マネージド | VPC外 | Step Functions Map State | スタブモード（外部API不要） |
| Lambda (Combiner) | AWS マネージド | VPC外 | Step Functions | パブリックサブネット相当 |
| CloudWatch Logs | AWS マネージド | VPC外 | Lambda自動送信 | ログ保管 |

**アクセスフロー（Sandbox）**:
```
社内（豊洲） → インターネット → S3 (input/)
                                   ↓
                              EventBridge
                                   ↓
                            Step Functions
                                   ↓
                              Lambda (VPC外)
                                   ↓
                            S3 (output/) → 社内（豊洲）
```

**現在の状況**:
- すべてのコンポーネントがVPC外のマネージドサービスとして動作
- Processor Lambdaはスタブモードで動作（外部API呼び出し不要）
- S3へのアクセスはインターネット経由（IAMで制御）

---

### Production環境（今後の予定）

| コンポーネント | 配置場所 | ネットワーク | アクセス元 | 備考 |
|---------------|---------|-------------|-----------|------|
| S3 Bucket | AWS グローバル | パブリック（IAM制御） | • 社内ネットワーク（豊洲）<br>• AWS Console | Sandboxと同じ |
| EventBridge | AWS マネージド | VPC外 | S3イベント | Sandboxと同じ |
| Step Functions | AWS マネージド | VPC外 | EventBridge | Sandboxと同じ |
| Lambda (Splitter) | AWS マネージド | VPC外 | Step Functions | VPC不要 |
| **Lambda (Processor)** | **VPC内** | **プライベートサブネット** | Step Functions Map State | **LiteLLM API呼び出しのため** |
| Lambda (Combiner) | AWS マネージド | VPC外 | Step Functions | VPC不要 |
| **VPC Endpoint** | **VPC内** | **プライベートサブネット** | Processor Lambda | **LiteLLM API接続用** |
| LiteLLM API | 社内/AWS | 要確認 | Processor Lambda | askul-gpt.askul-it.com |

**アクセスフロー（Production）**:
```
社内（豊洲） → インターネット → S3 (input/)
                                   ↓
                              EventBridge
                                   ↓
                            Step Functions
                                   ↓
                  ┌─────────────────┴─────────────────┐
                  │                                   │
            Splitter (VPC外)               Combiner (VPC外)
                  │                                   │
                  ↓                                   ↓
           Processor (VPC内) ────→ LiteLLM API
                  │              (VPC Endpoint経由)
                  ↓
            S3 (results/, output/) → 社内（豊洲）
```

---

### VPC構成（Production環境）

```
┌─────────────────────────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)                        │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Availability Zone: ap-northeast-1a                  │   │
│  │                                                        │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │  Private Subnet (10.0.1.0/24)                  │  │   │
│  │  │                                                  │  │   │
│  │  │  ┌──────────────────────────────────────┐      │  │   │
│  │  │  │  Processor Lambda (×500 並列)        │      │  │   │
│  │  │  │  - ENI: 10.0.1.x                     │      │  │   │
│  │  │  │  - Security Group: processor-sg      │      │  │   │
│  │  │  └─────────────┬────────────────────────┘      │  │   │
│  │  │                │                                 │  │   │
│  │  │                ↓ HTTPS (443)                    │  │   │
│  │  │  ┌──────────────────────────────────────┐      │  │   │
│  │  │  │  VPC Endpoint (LiteLLM API)          │      │  │   │
│  │  │  │  - Interface Endpoint                │      │  │   │
│  │  │  │  - Security Group: endpoint-sg       │      │  │   │
│  │  │  └──────────────────────────────────────┘      │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  VPC Endpoint (S3)                                    │   │
│  │  - Gateway Endpoint (無料)                            │   │
│  │  - Route Table: private-rt                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**VPC構成の詳細**:

| 項目 | 値 | 備考 |
|------|-----|------|
| VPC CIDR | 10.0.0.0/16 | プライベートIPアドレス空間 |
| Availability Zone | ap-northeast-1a | 単一AZ（コスト削減） |
| Private Subnet | 10.0.1.0/24 | Processor Lambda配置用 |
| NAT Gateway | 不要 | VPC Endpoint使用のため |
| Internet Gateway | 不要 | 外部インターネット接続不要 |

---

### Security Group 設定（Production）

| Security Group | タイプ | プロトコル | ポート | 送信先/送信元 | 説明 |
|---------------|--------|----------|--------|--------------|------|
| processor-sg | Outbound | HTTPS | 443 | VPC Endpoint (endpoint-sg) | LiteLLM API呼び出し |
| processor-sg | Outbound | HTTPS | 443 | S3 (pl-61a54008) | S3アクセス（Gateway Endpoint経由） |
| endpoint-sg | Inbound | HTTPS | 443 | processor-sg | Processor Lambdaからの接続許可 |

**セキュリティポイント**:
- Processor Lambdaはプライベートサブネット内で動作（インターネット接続なし）
- LiteLLM APIへのアクセスはVPC Endpoint経由（プライベート接続）
- S3へのアクセスはGateway Endpoint経由（データ転送料無料）
- Security Groupで最小権限の原則を適用

---

### LiteLLM API の接続確認事項

以下の情報が必要です（インフラ構築前に確認）：

| 項目 | 確認内容 | 備考 |
|------|---------|------|
| API エンドポイント | askul-gpt.askul-it.com の配置場所 | 社内サーバー or AWS内 |
| 接続方式 | プライベート接続 or インターネット経由 | VPC Endpoint設定に影響 |
| 認証方式 | API Key or IAM認証 | Secrets Manager格納予定 |
| ネットワーク制限 | 送信元IP制限の有無 | Lambda ENIの固定IP必要か |
| TLS/SSL | 証明書の種類 | プライベート証明書の場合、追加設定必要 |

---

### コスト影響（Production環境でVPC使用時）

| 項目 | Sandbox (VPC外) | Production (VPC内) | 差分 |
|------|----------------|-------------------|------|
| Lambda実行コスト | 同じ | 同じ | - |
| VPC Endpoint (Interface) | $0 | ~$7.2/月 | +$7.2 |
| VPC Endpoint (Gateway) | $0 | $0 (無料) | - |
| NAT Gateway | $0 | $0 (不使用) | - |
| データ転送 | 同じ | 同じ | - |
| **月額合計** | ~$9.11 | **~$16.31** | **+$7.2** |

**注意**: VPC Endpoint (Interface) は時間課金（$0.01/時間 ≈ $7.2/月）

---

## 構築手順（Production環境）

### Phase 1: VPC構築
1. VPC作成 (10.0.0.0/16)
2. Private Subnet作成 (10.0.1.0/24, ap-northeast-1a)
3. Route Table作成
4. VPC Endpoint (Gateway) 作成 - S3用
5. VPC Endpoint (Interface) 作成 - LiteLLM API用
6. Security Group作成 (processor-sg, endpoint-sg)

### Phase 2: Lambda設定変更
1. Processor Lambda をVPC内に配置
2. VPC設定: Private Subnet + processor-sg
3. 環境変数: LITELLM_MODE=production
4. Secrets Manager: API認証情報設定
5. タイムアウト: 90秒維持

### Phase 3: 接続テスト
1. テストイベントで1行処理
2. LiteLLM API接続確認
3. CloudWatch Logsでレスポンス確認
4. 大規模テスト（100行 → 1,000行 → 10,000行）

---

**質問事項**:
1. LiteLLM API (askul-gpt.askul-it.com) はどこに配置されていますか？
2. プライベート接続が必要ですか？それともインターネット経由で可能ですか？
3. 送信元IP制限はありますか？（Lambda ENIの固定IP必要性）
4. 認証方式はAPI Keyですか？それとも他の方式ですか？

---

**このセクションをConfluenceページの「インフラ構成」の後に挿入してください。**
