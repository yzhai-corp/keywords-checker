# Step Functions アーキテクチャ - デプロイ手順

このドキュメントは、AWS Step Functionsを使用したKeywords Checkerのデプロイ手順を説明します。

## 目次

1. [前提条件](#前提条件)
2. [ビルド](#ビルド)
3. [IAMロールの作成](#iamロールの作成)
4. [Lambda関数の作成](#lambda関数の作成)
5. [Step Functionsの作成](#step-functionsの作成)
6. [S3トリガーの設定（オプション）](#s3トリガーの設定オプション)
7. [テスト](#テスト)
8. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

### 必要なツール

- Python 3.13以上
- AWS CLI（設定済み）
- AWSコンソールへのアクセス権限

### 必要なAWSリソース

- S3バケット（input/, output/, results/フォルダ用）

### ビルド確認

```bash
# step-functionsディレクトリに移動
cd step-functions

# skillsフォルダが存在することを確認
ls -la skills/商品コピーチェック/

# 期待される出力:
# SKILL.md
# references/ (200+ファイル)
```

---

## ビルド

### 1. ビルドスクリプトの実行

```bash
cd step-functions
./build.sh
```

**生成物:**
- `build/skills-layer.zip` (約170KB) - Lambda Layer
- `build/splitter.zip` (約43MB)
- `build/processor.zip` (約30MB)
- `build/combiner.zip` (約43MB)

---

## IAMロールの作成

### Step 1: Lambda Layer の作成

Lambda Layerは3つのLambda関数で共有されるSkillsファイルを含みます。

#### AWS Consoleでの作成

1. **Lambda Console → レイヤー → レイヤーの作成**

2. **レイヤーの設定:**
   - 名前: `keywords-checker-skills-layer-sf`
   - 説明: `Skills and reference files for keywords checker (Step Functions)`
   - 「.zipファイルをアップロード」を選択
   - `build/skills-layer.zip` を選択
   - 互換性のあるランタイム: `Python 3.13`
   - 互換性のあるアーキテクチャ: `x86_64`

3. **作成** をクリック

4. **Lambda Layer ARNをメモ:**
   ```
   arn:aws:lambda:ap-northeast-1:ACCOUNT_ID:layer:keywords-checker-skills-layer-sf:1
   ```

#### AWS CLIでの作成

```bash
aws lambda publish-layer-version \
  --layer-name keywords-checker-skills-layer-sf \
  --description "Skills and reference files for keywords checker (Step Functions)" \
  --zip-file fileb://build/skills-layer.zip \
  --compatible-runtimes python3.13 \
  --compatible-architectures x86_64
```

### Step 2: Lambda用IAMロールの作成

#### Splitter Lambda用ロール

**ロール名:** `keywords-checker-splitter-role`

**信頼ポリシー:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**権限ポリシー:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET/input/*"
    }
  ]
}
```

#### Processor Lambda用ロール

**ロール名:** `keywords-checker-processor-role`

**信頼ポリシー:** （Splitterと同じ）

**権限ポリシー:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET/results/*"
    }
  ]
}
```

#### Combiner Lambda用ロール

**ロール名:** `keywords-checker-combiner-role`

**信頼ポリシー:** （Splitterと同じ）

**権限ポリシー:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET/input/*",
        "arn:aws:s3:::YOUR-BUCKET/results/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET/output/*"
    }
  ]
}
```

### Step 2: Step Functions用IAMロールの作成

**ロール名:** `keywords-checker-stepfunctions-role`

**信頼ポリシー:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "states.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**権限ポリシー:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:ap-northeast-1:ACCOUNT_ID:function:keywords-checker-splitter",
        "arn:aws:lambda:ap-northeast-1:ACCOUNT_ID:function:keywords-checker-processor",
        "arn:aws:lambda:ap-northeast-1:ACCOUNT_ID:function:keywords-checker-combiner"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

---

## Lambda関数の作成

**重要:** Lambda関数のZIPファイルが50MBを超える場合、S3経由でアップロードする必要があります。

### 事前準備: ZIPファイルをS3にアップロード

```bash
# S3バケットを作成（まだ作成していない場合）
aws s3 mb s3://YOUR-DEPLOYMENT-BUCKET

# ZIPファイルをS3にアップロード
cd step-functions/build
aws s3 cp skills-layer.zip s3://YOUR-DEPLOYMENT-BUCKET/lambda-code/
aws s3 cp splitter.zip s3://YOUR-DEPLOYMENT-BUCKET/lambda-code/
aws s3 cp processor.zip s3://YOUR-DEPLOYMENT-BUCKET/lambda-code/
aws s3 cp combiner.zip s3://YOUR-DEPLOYMENT-BUCKET/lambda-code/
```

### Step 3: Splitter Lambda関数の作成

#### AWS Consoleでの作成（S3経由）

1. **Lambda Console → 関数の作成**
2. **一から作成**を選択
3. 基本的な情報:
   - 関数名: `keywords-checker-splitter`
   - ランタイム: `Python 3.13`
   - アーキテクチャ: `x86_64`
   - 実行ロール: `keywords-checker-splitter-role`

4. **関数の作成** をクリック

5. **コードのアップロード（S3経由）:**
   - 「アップロード元」→「Amazon S3の場所」を選択
   - Amazon S3 リンク URL: `https://s3.amazonaws.com/YOUR-DEPLOYMENT-BUCKET/lambda-code/splitter.zip`
   - または `s3://YOUR-DEPLOYMENT-BUCKET/lambda-code/splitter.zip`
   - 「保存」をクリック

6. **設定タブ → 一般設定 → 編集:**
   - メモリ: `2048 MB`
   - タイムアウト: `5分`
   - エフェメラルストレージ: `512 MB`

7. **環境変数の設定:**
   - `RESULTS_BUCKET` = `YOUR-BUCKET`

8. **保存**

#### AWS CLIでの作成（S3経由）

```bash
aws lambda create-function \
  --function-name keywords-checker-splitter \
  --runtime python3.13 \
  --role arn:aws:iam::ACCOUNT_ID:role/keywords-checker-splitter-role \
  --handler lambda_function.lambda_handler \
  --code S3Bucket=YOUR-DEPLOYMENT-BUCKET,S3Key=lambda-code/splitter.zip \
  --timeout 300 \
  --memory-size 2048 \
  --environment "Variables={RESULTS_BUCKET=YOUR-BUCKET}"
```

### Step 4: Processor Lambda関数の作成

#### AWS Consoleでの作成（S3経由）

1. **Lambda Console → 関数の作成**
2. **一から作成**を選択
3. 基本的な情報:
   - 関数名: `keywords-checker-processor`
   - ランタイム: `Python 3.13`
   - アーキテクチャ: `x86_64`
   - 実行ロール: `keywords-checker-processor-role`

4. **関数の作成** をクリック

5. **コードのアップロード（S3経由）:**
   - 「アップロード元」→「Amazon S3の場所」を選択
   - Amazon S3 リンク URL: `s3://YOUR-DEPLOYMENT-BUCKET/lambda-code/processor.zip`
   - 「保存」をクリック

6. **設定タブ → 一般設定 → 編集:**
   - メモリ: `1024 MB`
   - タイムアウト: `2分`
   - エフェメラルストレージ: `512 MB`

7. **環境変数の設定:**
   - `RESULTS_BUCKET` = `YOUR-BUCKET`
   - `LITELLM_MODE` = `stub`
   - `LITELLM_API_BASE` = `https://askul-gpt.askul-it.com/v1`
   - `LITELLM_MODEL` = `gpt-5-mini`
   - `OPENAI_API_KEY` = `sk-xxxxxx`

8. **同時実行数の設定:**
   - 「同時実行数」→「予約済み同時実行数を編集」
   - 予約済み同時実行数: `500`

9. **Lambda Layerの追加:**
   - 「レイヤー」→「レイヤーを追加」
   - 「カスタムレイヤー」を選択
   - レイヤー: `keywords-checker-skills-layer-sf`
   - バージョン: `1` (最新)
   - **または ARN を指定:**
     ```
     arn:aws:lambda:ap-northeast-1:ACCOUNT_ID:layer:keywords-checker-skills-layer-sf:1
     ```
   - 「追加」をクリック

10. **保存**

#### AWS CLIでの作成（S3経由）

```bash
# Lambda関数を作成
aws lambda create-function \
  --function-name keywords-checker-processor \
  --runtime python3.13 \
  --role arn:aws:iam::ACCOUNT_ID:role/keywords-checker-processor-role \
  --handler lambda_function.lambda_handler \
  --code S3Bucket=YOUR-DEPLOYMENT-BUCKET,S3Key=lambda-code/processor.zip \
  --timeout 120 \
  --memory-size 1024 \
  --environment "Variables={RESULTS_BUCKET=YOUR-BUCKET,LITELLM_MODE=stub,LITELLM_API_BASE=https://askul-gpt.askul-it.com/v1,LITELLM_MODEL=gpt-5-mini,OPENAI_API_KEY=sk-xxxxxx}" \
  --layers arn:aws:lambda:ap-northeast-1:ACCOUNT_ID:layer:keywords-checker-skills-layer-sf:1

# 予約済み同時実行数を設定
aws lambda put-function-concurrency \
  --function-name keywords-checker-processor \
  --reserved-concurrent-executions 500
```

### Step 5: Combiner Lambda関数の作成

#### AWS Consoleでの作成（S3経由）

1. **Lambda Console → 関数の作成**
2. **一から作成**を選択
3. 基本的な情報:
   - 関数名: `keywords-checker-combiner`
   - ランタイム: `Python 3.13`
   - アーキテクチャ: `x86_64`
   - 実行ロール: `keywords-checker-combiner-role`

4. **関数の作成** をクリック

5. **コードのアップロード（S3経由）:**
   - 「アップロード元」→「Amazon S3の場所」を選択
   - Amazon S3 リンク URL: `s3://YOUR-DEPLOYMENT-BUCKET/lambda-code/combiner.zip`
   - 「保存」をクリック

6. **設定タブ → 一般設定 → 編集:**
   - メモリ: `2048 MB`
   - タイムアウト: `10分`
   - エフェメラルストレージ: `512 MB`

7. **環境変数の設定:**
   - `RESULTS_BUCKET` = `YOUR-BUCKET`

8. **保存**

#### AWS CLIでの作成（S3経由）

```bash
aws lambda create-function \
  --function-name keywords-checker-combiner \
  --runtime python3.13 \
  --role arn:aws:iam::ACCOUNT_ID:role/keywords-checker-combiner-role \
  --handler lambda_function.lambda_handler \
  --code S3Bucket=YOUR-DEPLOYMENT-BUCKET,S3Key=lambda-code/combiner.zip \
  --timeout 600 \
  --memory-size 2048 \
  --environment "Variables={RESULTS_BUCKET=YOUR-BUCKET}"
```

---

## Step Functionsの作成

### Step 6: State Machineの作成

#### AWS Consoleでの作成

1. **Step Functions Console → ステートマシン → ステートマシンの作成**

2. **作成方法を選択:**
   - **「自分で作成する」を選択** ✅

3. **定義方法を選択:**
   - 「コードでワークフローを記述」を選択
   - タイプ: **「標準」**

4. **定義:**
   - `state-machine.json` の内容をコピー
   - `ACCOUNT_ID` を実際のAWSアカウントIDに置き換え
   - 定義エディターに貼り付け

5. **ステートマシンの名前:**
   - `keywords-checker-state-machine`

6. **実行ロール:**
   - 「既存のロールを選択」
   - `keywords-checker-stepfunctions-role` を選択

7. **ロギング設定（オプション）:**
   - ログレベル: `ALL`
   - CloudWatch Logsロググループを作成

8. **ステートマシンの作成** をクリック

---

## S3トリガーの設定（オプション）

S3にファイルがアップロードされたら自動的にStep Functionsを起動する設定です。

### 推奨: EventBridge経由でStep Functionsを起動 ✅

EventBridgeを使用すると、Lambda関数を経由せずにStep Functionsを直接起動できます。

#### メリット
- ✅ Step Functionsを直接起動（中間Lambda不要）
- ✅ イベント履歴の確認が可能
- ✅ 柔軟なフィルタリング
- ✅ Dead Letter Queue対応
- ✅ 複数のターゲットに配信可能

#### Step 7-A: S3バケットでEventBridge通知を有効化

1. **S3 Console → バケット → プロパティ**

2. **イベント通知 → Amazon EventBridgeを有効にする:**
   - 「Amazon EventBridgeを有効にする」をON

3. **保存**

#### Step 7-B: EventBridge Ruleの作成

1. **EventBridge Console → ルール → ルールを作成**

2. **ルールの詳細:**
   - 名前: `keywords-checker-s3-trigger`
   - イベントバス: `default`
   - ルールタイプ: `イベントパターンを持つルール`

3. **イベントパターン:**

```json
{
  "source": ["aws.s3"],
  "detail-type": ["Object Created"],
  "detail": {
    "bucket": {
      "name": ["YOUR-BUCKET"]
    },
    "object": {
      "key": [{
        "prefix": "input/"
      }, {
        "suffix": ".xlsx"
      }]
    }
  }
}
```

4. **ターゲットを選択:**
   - ターゲットタイプ: `AWS サービス`
   - ターゲット: `Step Functions ステートマシン`
   - ステートマシン: `keywords-checker-state-machine`

5. **実行ロール:**
   - 「この特定のリソースに対して新しいロールを作成する」を選択
   - ロール名: `EventBridge-StepFunctions-keywords-checker`

6. **入力の設定（重要）:**
   - 「入力トランスフォーマーの設定」を選択
   - **入力パス:**
   ```json
   {
     "bucket": "$.detail.bucket.name",
     "key": "$.detail.object.key"
   }
   ```
   - **入力テンプレート:**
   ```json
   {
     "Records": [{
       "eventSource": "aws:s3",
       "s3": {
         "bucket": {"name": <bucket>},
         "object": {"key": <key>}
       }
     }]
   }
   ```

7. **ルールを作成** をクリック

#### 動作確認

```bash
# Excelファイルをアップロード
aws s3 cp examples/sample.xlsx s3://YOUR-BUCKET/input/

# Step Functionsの実行を確認
aws stepfunctions list-executions --state-machine-arn arn:aws:states:ap-northeast-1:ACCOUNT_ID:stateMachine:keywords-checker-state-machine --max-results 1
```

---

### 代替案1: Lambda直接S3トリガー（シンプル）

EventBridgeを使わず、Lambda SplitterにS3トリガーを直接追加する方法です。

#### Step 7-1: S3トリガーをLambda Splitterに追加

1. **Lambda Console → Splitter関数 → トリガーを追加**

2. **トリガーの設定:**
   - トリガーのソース: `S3`
   - バケット: `YOUR-BUCKET`
   - イベントタイプ: `すべてのオブジェクト作成イベント`
   - プレフィックス: `input/`
   - サフィックス: `.xlsx`

3. **追加** をクリック

#### Step 7-2: Splitter関数を修正してStep Functionsを起動

Splitter関数の最後にStep Functions起動コードを追加:

```python
import boto3

stepfunctions = boto3.client('stepfunctions')

def lambda_handler(event, context):
    # 既存のSplitter処理
    result = {
        'execution_id': execution_id,
        'input_bucket': bucket,
        'input_key': input_key,
        'output_bucket': bucket,
        'output_key': output_key,
        'total_rows': total_rows,
        'rows': rows_data
    }
    
    # Step Functionsを起動
    sf_response = stepfunctions.start_execution(
        stateMachineArn='arn:aws:states:ap-northeast-1:ACCOUNT_ID:stateMachine:keywords-checker-state-machine',
        name=execution_id,
        input=json.dumps(result)
    )
    
    logger.info(f"Started Step Functions execution: {sf_response['executionArn']}")
    
    return result
```

#### 必要なIAM権限を追加

Splitterロールに以下を追加:

```json
{
  "Effect": "Allow",
  "Action": [
    "states:StartExecution"
  ],
  "Resource": "arn:aws:states:ap-northeast-1:ACCOUNT_ID:stateMachine:keywords-checker-state-machine"
}
```

---

### 代替案2: 中間Lambda（トリガー専用）

S3トリガーを受けてStep Functionsを起動する専用Lambda関数を作成する方法です。

#### Step 7-Lambda: トリガーLambda関数の作成

```python
import boto3
import json
import logging
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

stepfunctions = boto3.client('stepfunctions')

STATE_MACHINE_ARN = 'arn:aws:states:ap-northeast-1:ACCOUNT_ID:stateMachine:keywords-checker-state-machine'

def lambda_handler(event, context):
    """S3イベントを受けてStep Functionsを起動"""
    try:
        # S3イベントから情報を取得
        s3_event = event['Records'][0]['s3']
        bucket = s3_event['bucket']['name']
        key = unquote_plus(s3_event['object']['key'])
        
        logger.info(f"S3 event: s3://{bucket}/{key}")
        
        # Step Functionsに渡すイベントを構築
        sf_input = {
            'Records': [{
                'eventSource': 'aws:s3',
                's3': {
                    'bucket': {'name': bucket},
                    'object': {'key': key}
                }
            }]
        }
        
        # Step Functionsを起動
        response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(sf_input)
        )
        
        logger.info(f"Started Step Functions: {response['executionArn']}")
        
        return {
            'statusCode': 200,
            'executionArn': response['executionArn']
        }
        
    except Exception as e:
        logger.error(f"Failed to start Step Functions: {str(e)}", exc_info=True)
        raise
```

この関数にS3トリガーを追加し、IAMロールに`states:StartExecution`権限を付与します。

---

## テスト

### Step 8: Splitter Lambda関数の個別テスト

#### テストイベント

```json
{
  "bucket": "YOUR-BUCKET",
  "input_key": "input/sample.xlsx"
}
```

#### 期待される出力

```json
{
  "execution_id": "20260204-143025-abc123",
  "input_bucket": "YOUR-BUCKET",
  "input_key": "input/sample.xlsx",
  "output_bucket": "YOUR-BUCKET",
  "output_key": "output/result_20260204_143025_sample.xlsx",
  "total_rows": 130,
  "rows": [
    {
      "row_index": 0,
      "変更後_キャッチコピーBtoC": "値",
      ...
    },
    ...
  ]
}
```

### Step 9: Processor Lambda関数の個別テスト

#### テストイベント

```json
{
  "execution_id": "test-20260204",
  "row_index": 0,
  "row_data": {
    "変更後_キャッチコピーBtoC": "ウイルス予防に効果的",
    "変更後_キャッチコピーBtoB": "免疫力アップ",
    "変更後_仕様スペック": "",
    "変更後_商品説明文": "",
    "変更後_商品名": "サプリメント",
    "変更後_検索用キーワード": "",
    "変更後_使用上の注意": "",
    "変更後_アスクルおススメポイント": ""
  }
}
```

#### 期待される出力

```json
{
  "row_index": 0,
  "status": "success",
  "s3_key": "results/test-20260204/0.json"
}
```

#### S3に保存された結果を確認

```bash
aws s3 cp s3://YOUR-BUCKET/results/test-20260204/0.json -
```

### Step 10: Step Functions全体のテスト

#### Step Functions Consoleでの実行

1. **Step Functions Console → ステートマシン → keywords-checker-state-machine**

2. **実行の開始** をクリック

3. **入力:**

```json
{
  "bucket": "YOUR-BUCKET",
  "input_key": "input/sample.xlsx"
}
```

4. **実行の開始** をクリック

5. **実行の詳細:**
   - グラフビューで進捗を確認
   - 各ステップの入出力を確認
   - エラーがあればログを確認

6. **完了後、S3を確認:**

```bash
aws s3 ls s3://YOUR-BUCKET/output/
aws s3 ls s3://YOUR-BUCKET/results/20260204-143025-abc123/
```

### Step 11: S3トリガーでのテスト

#### Excelファイルをアップロード

```bash
aws s3 cp examples/sample.xlsx s3://YOUR-BUCKET/input/
```

#### Step Functionsの実行を確認

1. **Step Functions Console → 実行**
2. 最新の実行が自動的に開始されていることを確認
3. 完了後、S3のoutput/フォルダに結果ファイルが生成されていることを確認

---

## トラブルシューティング

### CloudWatch Logsの確認

各Lambda関数のログを確認:

```bash
# Splitter
aws logs tail /aws/lambda/keywords-checker-splitter --follow

# Processor
aws logs tail /aws/lambda/keywords-checker-processor --follow

# Combiner
aws logs tail /aws/lambda/keywords-checker-combiner --follow
```

### よくあるエラー

#### 1. `Unable to import module 'lambda_function'`

**原因:** Lambda関数のパッケージが正しくビルドされていない

**解決策:**
```bash
cd step-functions
rm -rf build
./build.sh
# 生成されたZIPファイルを再アップロード
```

#### 2. `No module named 'pydantic_core'`

**原因:** Platform-specific依存関係が正しくインストールされていない

**解決策:** `build.sh` で `--platform manylinux2014_x86_64` フラグが使用されていることを確認

#### 3. `Access Denied` (S3)

**原因:** IAMロールにS3権限がない

**解決策:** IAMロールの権限ポリシーを確認して、必要なS3バケット/プレフィックスへのアクセスを許可

#### 4. `Execution failed (Processor)`

**原因:** Lambda Layerが正しくアタッチされていない

**解決策:**
- Processor関数にLambda Layer `keywords-checker-skills-layer` が追加されているか確認
- Layer ARNが正しいか確認

#### 5. `Too Many Requests` (Processor並列実行時)

**原因:** 同時実行数の制限に到達

**解決策:**
- Processor関数の予約済み同時実行数を500に設定
- Step Functionsの `MaxConcurrency` を調整（state-machine.jsonで500に設定済み）

#### 6. Step Functionsの実行が失敗

**CloudWatch Logsで詳細を確認:**

```bash
aws logs tail /aws/stepfunctions/keywords-checker-state-machine --follow
```

### Lambda関数のバージョン確認

```bash
# Python バージョン確認
aws lambda get-function-configuration --function-name keywords-checker-splitter | jq .Runtime
aws lambda get-function-configuration --function-name keywords-checker-processor | jq .Runtime
aws lambda get-function-configuration --function-name keywords-checker-combiner | jq .Runtime
```

全て `python3.13` であることを確認

---

## Dev/Production環境への移行

### VPC設定（本番環境のみ）

本番環境では内部LLM APIにアクセスするためVPC設定が必要です:

1. **VPCとサブネット作成**
   - Direct Connect/VPN経由で内部ネットワークにアクセス可能なVPC

2. **セキュリティグループ作成**
   - アウトバウンド: HTTPS (443) を内部APIエンドポイントに許可

3. **Processor Lambda関数のVPC設定:**
   - VPC: 作成したVPC
   - サブネット: プライベートサブネット（複数AZ推奨）
   - セキュリティグループ: 作成したセキュリティグループ

4. **環境変数を本番用に変更:**
   - `LITELLM_MODE` = `production`（スタブモードオフ）
   - `LITELLM_API_BASE` = 本番APIエンドポイント
   - `OPENAI_API_KEY` = 本番APIキー

5. **IAMロールにVPC権限を追加:**

```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:CreateNetworkInterface",
    "ec2:DescribeNetworkInterfaces",
    "ec2:DeleteNetworkInterface"
  ],
  "Resource": "*"
}
```

### スタブモード → 本番モードの切り替え

```bash
# 環境変数を更新
aws lambda update-function-configuration \
  --function-name keywords-checker-processor \
  --environment "Variables={RESULTS_BUCKET=YOUR-BUCKET,LITELLM_MODE=production,LITELLM_API_BASE=https://askul-gpt.askul-it.com/v1,LITELLM_MODEL=gpt-5-mini,OPENAI_API_KEY=YOUR-API-KEY}"
```

---

## まとめ

このデプロイ手順により、Step Functions + Lambdaアーキテクチャが完全に稼働します。

**アーキテクチャの利点:**
- ✅ 15分のタイムアウト制限なし
- ✅ 自動並列処理（最大500並列）
- ✅ 視覚的な進捗確認
- ✅ 自動リトライとエラーハンドリング
- ✅ S3ベースのデータ保存（256KB制限回避）

**次のステップ:**
- Sandbox環境で動作確認
- Dev環境に展開
- 本番環境へ移行（VPC設定 + 本番API接続）
