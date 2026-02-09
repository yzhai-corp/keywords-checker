# Confluenceコメント対応サマリー

## コメント内容
> あとはネットワーク的にどこに配置するのかがわかると構築に進めると思います。
> どこ（例：VPC内/外、プライベート/パブリックサブネット）に配置して、どこ（社内では豊洲/インターネット）からアクセスされるのかなどが知りたいです。

## 対応内容

### 1. ドキュメント更新

#### AWS_INFRASTRUCTURE.md に追加
- **ネットワーク構成セクション**を新規追加
  - Sandbox環境の配置表（VPC外構成）
  - Production環境の配置表（VPC構成）
  - アクセスフロー図（テキスト形式）
  - VPC構成図（ASCII art）
  - Security Group設定表

- **アーキテクチャ図を2つに分割**
  - Sandbox環境（現在・VPC外構成）の図
  - Production環境（今後・VPC構成）の図

#### README.md に追加
- ネットワーク構成への参照リンクを追加
- Sandbox/Production環境の違いを明記

### 2. Confluence更新用ドキュメント作成

**ファイル**: `docs/CONFLUENCE_NETWORK_UPDATE.md`

このファイルには以下が含まれています：

#### ネットワーク構成
1. **Sandbox環境（現在）**
   - 配置場所: すべてVPC外
   - アクセス元: 社内（豊洲）→ インターネット → S3
   - 特徴: スタブモード、外部API不要

2. **Production環境（今後）**
   - 配置場所: Processor Lambdaのみ VPC内プライベートサブネット
   - アクセス元: 同Sandbox（S3経由）
   - VPC Endpoint: LiteLLM API接続用（Interface Endpoint）
   - S3アクセス: Gateway Endpoint経由（プライベート接続）

#### VPC構成詳細
- VPC CIDR: 10.0.0.0/16
- Private Subnet: 10.0.1.0/24 (ap-northeast-1a)
- NAT Gateway: 不要
- Internet Gateway: 不要

#### Security Group設定
| Security Group | タイプ | ポート | 送信先/送信元 |
|---------------|--------|--------|--------------|
| processor-sg | Outbound | 443 | VPC Endpoint |
| processor-sg | Outbound | 443 | S3 (Gateway Endpoint) |
| endpoint-sg | Inbound | 443 | processor-sg |

#### コスト影響
- Sandbox: $9.11/月
- Production: $16.31/月（+$7.2 VPC Endpoint）

#### 構築手順
1. Phase 1: VPC構築
2. Phase 2: Lambda設定変更
3. Phase 3: 接続テスト

### 3. LiteLLM API 接続確認事項リスト

以下の情報を確認する必要がある旨を明記：
1. askul-gpt.askul-it.com の配置場所（社内 or AWS内）
2. 接続方式（プライベート or インターネット）
3. 送信元IP制限の有無
4. 認証方式（API Key or その他）
5. TLS/SSL証明書の種類

## Confluenceページへの反映方法

1. Confluence ページを編集モードで開く
   - URL: https://askul.atlassian.net/wiki/spaces/TEC/pages/223052388/AWS

2. `docs/CONFLUENCE_NETWORK_UPDATE.md` の内容をコピー

3. 「インフラ構成」セクションの後ろに貼り付け

4. Mermaid図は Confluence の Code Block として挿入
   - 言語: text または plaintext

5. 表は Confluenceの標準テーブル機能で整形

## 変更ファイル一覧

1. `docs/AWS_INFRASTRUCTURE.md`
   - ネットワーク構成セクション追加
   - アーキテクチャ図を2つに分割

2. `step-functions/README.md`
   - ネットワーク構成への参照追加

3. `docs/CONFLUENCE_NETWORK_UPDATE.md`（新規作成）
   - Confluence貼り付け用のマークダウン

## 次のアクションアイテム

### インフラチームへの確認事項
1. ☐ LiteLLM API (askul-gpt.askul-it.com) の配置場所確認
2. ☐ プライベート接続が必要か確認
3. ☐ 送信元IP制限の有無確認
4. ☐ 認証方式の確認（API Key or IAM）
5. ☐ TLS/SSL証明書の種類確認

### 構築準備
1. ☐ VPC CIDR範囲の承認（10.0.0.0/16）
2. ☐ Subnet CIDR範囲の承認（10.0.1.0/24）
3. ☐ Security Group ルールの承認
4. ☐ VPC Endpoint費用の承認（$7.2/月）

### 開発タスク
1. ☐ Production環境用のTerraform/CloudFormation作成
2. ☐ VPC構築
3. ☐ Processor Lambda VPC設定変更
4. ☐ 接続テスト実施
5. ☐ 大規模テスト（1,000行、10,000行）

## 補足資料

### アクセスフロー比較

**Sandbox（現在）**:
```
社内（豊洲） 
    → インターネット 
        → S3 
            → EventBridge 
                → Step Functions 
                    → Lambda (VPC外) 
                        → S3 
                            → 社内（豊洲）
```

**Production（今後）**:
```
社内（豊洲） 
    → インターネット 
        → S3 
            → EventBridge 
                → Step Functions 
                    → Processor Lambda (VPC内) 
                        → VPC Endpoint 
                            → LiteLLM API
                    → S3 
                        → 社内（豊洲）
```

### セキュリティポイント
- ☑ Processor Lambdaはプライベートサブネット（インターネット接続なし）
- ☑ LiteLLM APIへのアクセスはVPC Endpoint経由（プライベート接続）
- ☑ S3へのアクセスはGateway Endpoint経由（無料）
- ☑ Security Groupで最小権限の原則を適用
- ☑ API認証情報はSecrets Managerで管理

---

**作成日**: 2026年2月6日
**対応者**: GitHub Copilot
**Confluenceページ**: https://askul.atlassian.net/wiki/spaces/TEC/pages/223052388/AWS
