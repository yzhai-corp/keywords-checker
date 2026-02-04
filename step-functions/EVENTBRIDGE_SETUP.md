# EventBridge設定ガイド

## 概要

S3へのファイルアップロードをEventBridgeで検知し、Step Functionsを自動起動する設定手順です。

## アーキテクチャ

```
S3アップロード (input/*.xlsx)
  ↓
EventBridge通知
  ↓
EventBridge Rule (keywords-checker-s3-trigger)
  - イベントパターン: S3 Object Created
  - フィルター: input/*.xlsx
  - 入力トランスフォーマー
  ↓
Step Functions State Machine
  - keywords-checker-state-machine
  ↓
Splitter → Map(Processor) → Combiner
```

## 設定手順

### 1. S3バケットでEventBridge通知を有効化

#### AWS Console

1. **S3 Console** を開く
2. バケット名をクリック（例: `askul-sandbox-01-regulation-test-bucket`）
3. **プロパティ** タブを選択
4. **イベント通知** セクションまでスクロール
5. **Amazon EventBridgeを有効にする** をONに設定
6. **変更を保存**

#### AWS CLI

```bash
# EventBridge通知を有効化
aws s3api put-bucket-notification-configuration \
  --bucket YOUR-BUCKET \
  --notification-configuration '{
    "EventBridgeConfiguration": {}
  }'
```

### 2. EventBridge Ruleの作成

#### AWS Console

1. **EventBridge Console** を開く
2. **ルール** → **ルールを作成** をクリック

3. **ルールの詳細:**
   - 名前: `keywords-checker-s3-trigger`
   - 説明: `S3へのExcelアップロードでStep Functionsを起動`
   - イベントバス: `default`
   - ルールタイプ: `イベントパターンを持つルール`
   - **次へ** をクリック

4. **イベントパターン:**
   - イベントソース: `AWS のサービス`
   - AWSサービス: `Simple Storage Service (S3)`
   - イベントタイプ: `Amazon S3 イベント通知`
   - イベントタイプを指定: `Object Created`
   - **カスタムパターンを編集** をクリック

5. **イベントパターンJSON:**

```json
{
  "source": ["aws.s3"],
  "detail-type": ["Object Created"],
  "detail": {
    "bucket": {
      "name": ["askul-sandbox-01-regulation-test-bucket"]
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

   - **次へ** をクリック

6. **ターゲットを選択:**
   - ターゲットタイプ: `AWS サービス`
   - ターゲットを選択: `Step Functions ステートマシン`
   - ステートマシン: `keywords-checker-state-machine`

7. **実行ロール:**
   - **この特定のリソースに対して新しいロールを作成する** を選択
   - ロール名: `EventBridge-StepFunctions-keywords-checker`

8. **追加設定 → 入力の設定:**
   - **入力トランスフォーマーの設定** を選択
   
   **入力パス:**
   ```json
   {
     "bucket": "$.detail.bucket.name",
     "key": "$.detail.object.key"
   }
   ```
   
   **入力テンプレート:**
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

9. **次へ** → **ルールを作成** をクリック

#### AWS CLI

```bash
# EventBridge Ruleを作成
aws events put-rule \
  --name keywords-checker-s3-trigger \
  --description "Trigger Step Functions on S3 Excel upload" \
  --event-pattern '{
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {
        "name": ["askul-sandbox-01-regulation-test-bucket"]
      },
      "object": {
        "key": [{"prefix": "input/"}, {"suffix": ".xlsx"}]
      }
    }
  }'

# ターゲット（Step Functions）を追加
aws events put-targets \
  --rule keywords-checker-s3-trigger \
  --targets '[
    {
      "Id": "1",
      "Arn": "arn:aws:states:ap-northeast-1:ACCOUNT_ID:stateMachine:keywords-checker-state-machine",
      "RoleArn": "arn:aws:iam::ACCOUNT_ID:role/EventBridge-StepFunctions-keywords-checker",
      "InputTransformer": {
        "InputPathsMap": {
          "bucket": "$.detail.bucket.name",
          "key": "$.detail.object.key"
        },
        "InputTemplate": "{\"Records\": [{\"eventSource\": \"aws:s3\", \"s3\": {\"bucket\": {\"name\": <bucket>}, \"object\": {\"key\": <key>}}}]}"
      }
    }
  ]'
```

### 3. IAMロールの作成（自動作成されない場合）

#### 信頼ポリシー

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### 権限ポリシー

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution"
      ],
      "Resource": "arn:aws:states:ap-northeast-1:ACCOUNT_ID:stateMachine:keywords-checker-state-machine"
    }
  ]
}
```

## テスト

### 1. EventBridge Ruleの確認

```bash
# ルールの状態確認
aws events describe-rule --name keywords-checker-s3-trigger

# ターゲットの確認
aws events list-targets-by-rule --rule keywords-checker-s3-trigger
```

### 2. S3にファイルをアップロード

```bash
# テストファイルをアップロード
aws s3 cp examples/sample.xlsx s3://askul-sandbox-01-regulation-test-bucket/input/

# または
aws s3 sync examples/ s3://askul-sandbox-01-regulation-test-bucket/input/ --exclude "*" --include "*.xlsx"
```

### 3. Step Functionsの実行を確認

#### AWS Console

1. **Step Functions Console** を開く
2. **ステートマシン** → `keywords-checker-state-machine` をクリック
3. **実行** タブで最新の実行を確認
4. **実行の詳細** をクリックして進捗を確認

#### AWS CLI

```bash
# 最新の実行を確認
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:ap-northeast-1:ACCOUNT_ID:stateMachine:keywords-checker-state-machine \
  --max-results 5

# 実行の詳細を確認
aws stepfunctions describe-execution \
  --execution-arn arn:aws:states:ap-northeast-1:ACCOUNT_ID:execution:keywords-checker-state-machine:EXECUTION_NAME
```

### 4. EventBridgeのイベント履歴を確認

#### AWS Console

1. **EventBridge Console** を開く
2. **イベント** → **イベント履歴** をクリック
3. フィルター: 
   - イベントソース: `aws.s3`
   - イベント名: `Object Created`
4. 該当するイベントをクリックして詳細を確認

## トラブルシューティング

### EventBridge通知が有効化されていない

**症状:** S3にファイルをアップロードしてもEventBridgeイベントが発火しない

**確認方法:**
```bash
aws s3api get-bucket-notification-configuration --bucket YOUR-BUCKET
```

**期待される出力:**
```json
{
  "EventBridgeConfiguration": {}
}
```

**解決策:** S3バケットのプロパティでEventBridge通知を有効化

### イベントパターンがマッチしない

**症状:** EventBridgeイベントは発火するが、Ruleがトリガーされない

**デバッグ:**
1. EventBridge Console → イベント履歴で実際のイベントを確認
2. イベントパターンと比較
3. プレフィックス/サフィックスが正しいか確認

**よくある問題:**
- プレフィックスに末尾の`/`が不足: `input` → `input/`
- サフィックスの大文字小文字: `.xlsx` vs `.XLSX`
- バケット名の間違い

### Step Functionsが起動しない

**症状:** EventBridge Ruleは実行されるが、Step Functionsが起動しない

**確認方法:**
```bash
# EventBridge Ruleのメトリクスを確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=RuleName,Value=keywords-checker-s3-trigger \
  --start-time 2026-02-04T00:00:00Z \
  --end-time 2026-02-04T23:59:59Z \
  --period 3600 \
  --statistics Sum

# 失敗したイベントを確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name FailedInvocations \
  --dimensions Name=RuleName,Value=keywords-checker-s3-trigger \
  --start-time 2026-02-04T00:00:00Z \
  --end-time 2026-02-04T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

**解決策:**
- IAMロールの権限を確認（`states:StartExecution`）
- ターゲットのARNが正しいか確認
- 入力トランスフォーマーのJSON形式が正しいか確認

### 入力トランスフォーマーのエラー

**症状:** Step Functionsは起動するが、Splitter Lambdaでエラー

**CloudWatch Logsを確認:**
```bash
aws logs tail /aws/lambda/keywords-checker-splitter --follow
```

**期待される入力形式:**
```json
{
  "Records": [{
    "eventSource": "aws:s3",
    "s3": {
      "bucket": {"name": "bucket-name"},
      "object": {"key": "input/file.xlsx"}
    }
  }]
}
```

**デバッグ方法:**
1. Step Functions実行の入力を確認
2. Splitter Lambdaのログで受信したイベントを確認
3. 入力トランスフォーマーのテンプレートを修正

## メリット再確認

### EventBridge経由 vs Lambda直接S3トリガー

| 項目 | EventBridge | Lambda直接トリガー |
|------|-------------|-------------------|
| 設定 | 2ステップ（S3通知+Rule） | 1ステップ |
| イベント履歴 | ✅ 確認可能 | ❌ なし |
| 柔軟性 | ✅ 複雑なフィルター可能 | ⚠️ 基本的なフィルターのみ |
| 複数ターゲット | ✅ 同じイベントで複数起動 | ❌ 1対1 |
| Step Functions直接起動 | ✅ 可能 | ❌ 中間Lambda必要 |
| DLQ | ✅ 対応 | ⚠️ Lambda側で設定 |
| コスト | わずかに高い（$1/百万イベント） | わずかに安い |

## まとめ

EventBridge経由のメリット:
- ✅ **疎結合**: S3とStep Functionsを直接接続
- ✅ **可視性**: イベント履歴で監視とデバッグが容易
- ✅ **拡張性**: 同じS3イベントで複数の処理を起動可能
- ✅ **保守性**: イベント駆動アーキテクチャのベストプラクティス

推奨される環境:
- **Sandbox/Dev/Production全て**: EventBridge経由を推奨
- **小規模テスト**: Lambda直接トリガーも可

次のステップ:
1. この設定を完了
2. S3にファイルをアップロードしてテスト
3. EventBridgeコンソールとStep Functionsコンソールで動作確認
