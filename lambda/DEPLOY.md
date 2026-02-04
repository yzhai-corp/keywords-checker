# AWS Lambda デプロイガイド

## 概要

このドキュメントは、Keywords CheckerのバックエンドをAWS Lambdaにデプロイする手順を説明します。

### アーキテクチャ

```
S3 Bucket (askul-sandbox-01-regulation-test-bucket)
    ↓ (input Excel)
Lambda1 (keywords-checker-lambda1)
    - Excelファイルを読み込み、行ごとに処理
    - 各行についてLambda2を呼び出し
    - 結果を統合してExcelファイルを作成
    - S3にアップロード
    ↓ (並列呼び出し)
Lambda2 (keywords-checker-lambda2) ×複数
    - キーワード検索
    - LLM APIにリクエスト
    - 結果を返す
```

## 準備

### 1. 必要なツール

- Python 3.10以上
- AWS CLI (設定済み)
- zip コマンド

### 2. ネットワーク要件

**重要**: Lambda2は社内APIエンドポイント (`askul-gpt.askul-it.com`) にアクセスするため、以下のネットワーク設定が必要です：

#### 必須要件
- Lambda2をVPCに配置
- 社内ネットワークへの接続（以下のいずれか）：
  - AWS Direct Connect
  - Site-to-Site VPN
  - Client VPN

#### 前提条件の確認
デプロイ前に以下を確認してください：

1. **VPC設定**
   - VPC ID（例: vpc-xxxxx）
   - プライベートサブネット × 2つ以上（例: subnet-xxxxx, subnet-yyyyy）
   - セキュリティグループ ID（例: sg-xxxxx）

2. **社内ネットワーク接続**
   - Direct ConnectまたはVPN接続が確立済み
   - `askul-gpt.askul-it.com` への通信が許可されている

3. **インターネットアクセス（外部ライブラリ用）**
   - NATゲートウェイまたはNATインスタンス（pip installで依存関係をダウンロードする場合）

### 3. VPC設定の準備（Lambda2用）

Lambda2は社内API (`askul-gpt.askul-it.com`) にアクセスするため、以下の情報を事前に確認してください：

#### 必要な情報
1. **VPC ID**: 社内ネットワークに接続されているVPC
   - 例: `vpc-0123456789abcdef0`
   - 確認方法: VPC Console → Your VPCs

2. **サブネット ID**: プライベートサブネット × 2つ以上（異なるAZ）
   - 例: `subnet-0123456789abcdef0 (ap-northeast-1a)`
   - 例: `subnet-0123456789abcdef1 (ap-northeast-1c)`
   - 確認方法: VPC Console → Subnets → Type: Private

3. **セキュリティグループ ID**: Lambda2用のセキュリティグループ
   - 例: `sg-0123456789abcdef0`
   - 必要なルール:
     ```
     Outbound:
     - HTTPS (443) → 0.0.0.0/0 または社内ネットワークCIDR
     - (オプション) All traffic → 0.0.0.0/0 (NAT Gateway経由のインターネットアクセス用)
     ```
   - 確認方法: EC2 Console → Security Groups

4. **ルートテーブル**: サブネットのルートテーブルに社内ネットワークへのルートが設定されているか
   - 確認方法: VPC Console → Route Tables → Routes
   - 必要なルート例:
     ```
     Destination: 10.0.0.0/8 → Target: vgw-xxxxx (Virtual Private Gateway)
     Destination: 172.16.0.0/12 → Target: tgw-xxxxx (Transit Gateway)
     ```

#### ネットワーク接続の確認

社内ネットワークへの接続方法を確認してください：

- **AWS Direct Connect**: VPC → Virtual Private Gateway → Direct Connect Gateway
- **Site-to-Site VPN**: VPC → Virtual Private Gateway → Customer Gateway
- **Transit Gateway**: VPC → Transit Gateway Attachment → 社内ネットワーク

### 4. ディレクトリ構成

```
lambda/
├── lambda1/
│   ├── lambda_function.py
│   └── requirements.txt
├── lambda2/
│   ├── lambda_function.py
│   └── requirements.txt
└── build/
    ├── lambda1.zip
    └── lambda2.zip
```

## デプロイ手順

### Step 1: Lambda Layerの準備

SKILLファイルとreferenceファイルをLambda Layerとして配置します。

```bash
cd /Users/abi01711/workspace/keywords-checker

# Layerディレクトリを作成
mkdir -p lambda/layer/python/skills
cp -r backend/skills/商品コピーチェック lambda/layer/python/skills/

# Layerをzip化
cd lambda/layer
zip -r ../skills-layer.zip .
cd ../..
```

### Step 2: Lambda1のビルド

```bash
cd lambda/lambda1

# 依存関係をインストール
mkdir -p package
pip install -r requirements.txt -t package/

# lambda_function.pyをpackageにコピー
cp lambda_function.py package/

# zipファイルを作成
cd package
zip -r ../../build/lambda1.zip .
cd ../..
```

### Step 3: Lambda2のビルド

```bash
cd lambda/lambda2

# 依存関係をインストール
mkdir -p package
pip install -r requirements.txt -t package/

# lambda_function.pyをpackageにコピー
cp lambda_function.py package/

# zipファイルを作成
cd package
zip -r ../../build/lambda2.zip .
cd ../..
```

### Step 4: Lambda Layerの作成（AWS Console）

**重要**: Lambda Layerにはロール（IAMロール）は不要です。Layerはただのコードライブラリです。

1. AWS Consoleにログイン
2. Lambda → Layers → Create layer
3. 以下を設定：
   - Name: `keywords-checker-skills-layer`
   - Upload: `lambda/skills-layer.zip`
   - Compatible runtimes: `Python 3.10`, `Python 3.11`
4. Create

### Step 5: Lambda2の作成（AWS Console）

**Lambda2の役割**: Lambda1から呼び出されてLLM APIにリクエストするだけです。
S3やLambda呼び出しの権限は不要で、基本的な実行ロールのみで十分です。

**重要**: Lambda2は社内API (`askul-gpt.askul-it.com`) にアクセスするため、VPC設定が必須です。

1. Lambda → Functions → Create function
2. 基本設定：
   - Function name: `keywords-checker-lambda2`
   - Runtime: `Python 3.13`
   - Architecture: `x86_64`
   - **Permissions**: デフォルトの実行ロール（自動作成される）でOK
3. Code → Upload from → .zip file → `lambda/build/lambda2.zip`
4. Configuration → Layers → Add a layer
   - Custom layers → `keywords-checker-skills-layer`
5. Configuration → General configuration
   - Memory: `1024 MB`
   - Timeout: `5 minutes`
6. Configuration → Environment variables
   - `LITELLM_API_BASE`: `https://askul-gpt.askul-it.com/v1`
   - `LITELLM_MODEL`: `gpt-5-mini`
   - `OPENAI_API_KEY`: `(実際のAPIキー)`

#### VPC設定（必須）

7. Configuration → VPC → Edit
   - **VPC**: 社内ネットワークに接続されているVPCを選択（例: `vpc-xxxxx`）
   - **Subnets**: プライベートサブネットを2つ以上選択
     - 推奨: 異なるAZのサブネット（例: `subnet-xxxxx (ap-northeast-1a)`, `subnet-yyyyy (ap-northeast-1c)`）
   - **Security groups**: 以下のルールを持つセキュリティグループを選択/作成
     ```
     Outbound Rules:
     - Type: HTTPS (443)
       Destination: 0.0.0.0/0 または社内ネットワークのCIDR
       Description: Allow access to askul-gpt.askul-it.com
     
     - Type: All traffic
       Destination: 0.0.0.0/0
       Description: (Optional) For internet access via NAT Gateway
     ```
   - Save

#### VPC設定後の確認

VPC設定後、以下を確認してください：

- ✅ Lambda2の実行ロールに `AWSLambdaVPCAccessExecutionRole` ポリシーが自動付与される
- ✅ ENI (Elastic Network Interface) が作成される（数分かかる場合があります）
- ✅ 社内API (`askul-gpt.askul-it.com`) への通信が可能

#### トラブルシューティング

**タイムアウトが発生する場合**:
1. Direct ConnectまたはVPN接続が確立されているか確認
2. セキュリティグループのアウトバウンドルールで443番ポートが許可されているか確認
3. ルートテーブルで社内ネットワークへのルートが設定されているか確認
4. CloudWatchログで「Network diagnostics」のログを確認：
   ```
   [INFO] DNS resolution successful: askul-gpt.askul-it.com -> xxx.xxx.xxx.xxx
   [INFO] HTTPS connection successful: 200
   ```
   または
   ```
   [ERROR] DNS resolution failed: ...
   [ERROR] HTTPS connection failed: ...
   ```

8. Configuration → Concurrency
   - Reserved concurrent executions: `100` (最大10000件を15分以内で処理するため)

**Lambda2のIAMロール**（自動作成されるデフォルトロールで十分）:
- CloudWatch Logsへの書き込み権限
- VPCアクセス権限（`AWSLambdaVPCAccessExecutionRole`）← VPC設定時に自動付与
- S3アクセスやLambda呼び出しの権限は不要

### Step 6: Lambda1の作成（AWS Console）

**Lambda1の役割**: S3からExcelを読み込み、Lambda2を呼び出し、結果をS3にアップロード

1. Lambda → Functions → Create function
2. 基本設定：
   - Function name: `keywords-checker-lambda1`
   - Runtime: `Python 3.10`
   - Architecture: `x86_64`
   - **Permissions**: 新しいロールを作成（次のステップで権限を追加）
3. Code → Upload from → .zip file → `lambda/build/lambda1.zip`
4. Configuration → Layers → Add a layer
   - Custom layers → `keywords-checker-skills-layer`
5. Configuration → General configuration
   - Memory: `2048 MB`
   - Timeout: `15 minutes`
6. Configuration → Environment variables
   - `BUCKET_NAME`: `askul-sandbox-01-regulation-test-bucket`
   - `LAMBDA2_FUNCTION_NAME`: `keywords-checker-lambda2`

### Step 7: Lambda1のIAMロール設定（重要）

Lambda1には以下の3つの権限が必要です：

1. **S3アクセス権限**: Excelファイルのダウンロードとアップロード
2. **Lambda呼び出し権限**: Lambda2を呼び出すため
3. **CloudWatch Logs権限**: ログ書き込み（デフォルトで付与）

#### 設定手順

1. Lambda1の関数ページ → Configuration → Permissions
2. Execution role の名前をクリック（IAMコンソールが開く）
3. Add permissions → Attach policies
4. 以下のポリシーをアタッチ：
   - `AWSLambdaBasicExecutionRole` (CloudWatch Logs用、すでに付与されている)

5. Add permissions → Create inline policy
6. JSON タブを選択して以下を貼り付け：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::askul-sandbox-01-regulation-test-bucket/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": "arn:aws:lambda:ap-northeast-1:*:function:keywords-checker-lambda2"
        }
    ]
}
```

7. Review policy → Name: `keywords-checker-lambda1-policy` → Create policy

### Step 8: S3トリガーの設定（推奨）

**この構成では、S3にファイルをアップロードすると自動的にLambda1が実行されます。**

Lambda1のコードはすでにS3トリガーとテストイベントの両方に対応しているため、すぐに使用できます。

#### S3トリガーの追加手順

1. Lambda1の関数ページ → Configuration → Triggers
2. Add trigger
3. 以下を設定：
   - Source: `S3`
   - Bucket: `askul-sandbox-01-regulation-test-bucket`
   - Event type: `All object create events`
   - Prefix: `input/` (inputフォルダ内のファイルのみ)
   - Suffix: `.xlsx` (Excelファイルのみ)
4. Add

#### 使用方法

ファイルをS3にアップロードするだけで自動処理が開始されます：

```bash
# ExcelファイルをS3にアップロード
aws s3 cp /path/to/your/file.xlsx s3://askul-sandbox-01-regulation-test-bucket/input/

# 処理が自動的に開始される
# 結果は output/result_YYYYMMDD_HHMMSS_file.xlsx として保存される
```

#### Lambda1のコード実装内容

Lambda1は以下の2つのイベントタイプに対応しています：

**A. S3トリガーイベント**
- S3からバケット名とファイル名を自動取得
- output_fileは自動生成: `output/result_YYYYMMDD_HHMMSS_元ファイル名.xlsx`
- 日本語ファイル名にも対応（URLデコード処理済み）

**B. テストイベント（手動実行）**
- `input_file`と`output_file`を指定して実行
- 開発・デバッグ時に便利

#### テスト実行（手動）

S3トリガーを設定した後も、手動実行が可能です：

```json
{
    "input_file": "input/sample.xlsx",
    "output_file": "output/result.xlsx"
}
```

### Step 9: Lambda1とLambda2のIAMロール設定まとめ

| Lambda関数 | 必要な権限 | 設定内容 |
|-----------|----------|---------|
| **Lambda2** | CloudWatch Logs書き込みのみ | デフォルトの実行ロール（`AWSLambdaBasicExecutionRole`）で十分 |
| **Lambda1** | 1. S3読み書き<br>2. Lambda2呼び出し<br>3. CloudWatch Logs書き込み | カスタムポリシーを追加（上記Step 7参照） |
| **Lambda Layer** | なし | Layerにはロールは不要 |

## テスト

### Lambda2のテスト（単体テスト）

Lambda2が正しく動作するか確認：

1. Lambda2の関数ページ → Test
2. Test eventを作成：

```json
{
    "row_index": 0,
    "product_message": "*商品名: テスト商品\n変更後_キャッチコピーBtoB: 健康を促進する商品です"
}
```

3. Test を実行
4. 実行結果に `"statusCode": 200` が表示されればOK

### Lambda1のテスト

#### 方法A: Test機能で手動実行

1. S3にテストExcelファイルをアップロード：
   ```bash
   aws s3 cp examples/sample.csv s3://askul-sandbox-01-regulation-test-bucket/input/sample.xlsx
   ```

2. Lambda1の関数ページ → Test
3. Test eventを作成：
   ```json
   {
       "input_file": "input/sample.xlsx",
       "output_file": "output/result.xlsx"
   }
   ```

4. Test を実行
5. 処理完了後、S3の `output/result.xlsx` を確認

#### 方法B: S3トリガーで自動実行（推奨、Step 8で設定済みの場合）

1. S3にExcelファイルをアップロード：
   ```bash
   aws s3 cp examples/sample.csv s3://askul-sandbox-01-regulation-test-bucket/input/test.xlsx
   ```

2. Lambda1が自動的に起動（数秒以内）

3. CloudWatch Logsでログを確認：
   ```bash
   aws logs tail /aws/lambda/keywords-checker-lambda1 --follow
   ```

4. 処理完了後、S3の `output/` フォルダに結果ファイルが作成される：
   ```bash
   # 結果ファイルを確認
   aws s3 ls s3://askul-sandbox-01-regulation-test-bucket/output/
   
   # 結果ファイルをダウンロード
   aws s3 cp s3://askul-sandbox-01-regulation-test-bucket/output/result_20260203_123456_test.xlsx ./
   ```

5. ログでS3トリガーが検出されたことを確認：
   ```
   INFO Lambda1 started. Event: {"Records": [...]}
   INFO Triggered by S3 event
   INFO S3 trigger: input/test.xlsx → output/result_20260203_123456_test.xlsx
   ```

## トラブルシューティング

### メモリ不足エラー

- Lambda1のメモリを3008 MBに増やす
- Lambda2のメモリを1536 MBに増やす

### タイムアウトエラー

- Lambda1のタイムアウトを15分に設定
- Lambda2の予約済み同時実行数を増やす

### 依存関係エラー

- requirements.txtの内容を確認
- pipのバージョンを最新にする

## コスト見積もり

- Lambda1: 2048 MB × 15分 × 月100回 = 約$X
- Lambda2: 1024 MB × 2分 × 月10000回 × 100並列 = 約$Y
- S3: 転送量に応じて

## 監視

CloudWatch Logsでログを確認：

```bash
# Lambda1のログ
aws logs tail /aws/lambda/keywords-checker-lambda1 --follow

# Lambda2のログ
aws logs tail /aws/lambda/keywords-checker-lambda2 --follow
```

## 更新手順

コードを更新した場合：

1. Step 2-3を再実行してzipファイルを再作成
2. AWS Console → Lambda → 該当関数 → Code → Upload from → .zip file
3. テストを実行して動作確認
