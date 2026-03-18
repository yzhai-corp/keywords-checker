#!/bin/bash
# EventBridge 設定スクリプト
# S3 の input/ フォルダに Excel ファイルがアップロードされたら Step Functions を自動起動

set -e

PROFILE="sandbox"
REGION="ap-northeast-1"
BUCKET_NAME="askul-sandbox-01-regulation-step-functions-bucket"
STATE_MACHINE_ARN="arn:aws:states:ap-northeast-1:730335237698:stateMachine:keywords-checker-state-machine"
RULE_NAME="keywords-checker-s3-trigger"

echo "=== EventBridge Setup for Step Functions ==="
echo "Profile: $PROFILE"
echo "Region: $REGION"
echo "Bucket: $BUCKET_NAME"
echo "State Machine: $STATE_MACHINE_ARN"
echo ""

# Step 1: S3 バケットで EventBridge 通知を有効化
echo "[1/4] S3 バケットで EventBridge 通知を有効化..."
aws s3api put-bucket-notification-configuration \
  --bucket "$BUCKET_NAME" \
  --notification-configuration '{
    "EventBridgeConfiguration": {}
  }' \
  --profile "$PROFILE" \
  --region "$REGION"

echo "✅ S3 EventBridge 通知が有効化されました"
echo ""

# Step 2: EventBridge Rule を作成
echo "[2/4] EventBridge Rule を作成..."
RULE_ARN=$(aws events put-rule \
  --name "$RULE_NAME" \
  --event-pattern '{
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {
        "name": ["'"$BUCKET_NAME"'"]
      },
      "object": {
        "key": [{
          "prefix": "input/"
        }, {
          "suffix": ".xlsx"
        }]
      }
    }
  }' \
  --state ENABLED \
  --description "Trigger Step Functions when Excel file is uploaded to input/ folder" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query 'RuleArn' \
  --output text)

echo "✅ EventBridge Rule が作成されました: $RULE_ARN"
echo ""

# Step 3: Step Functions に EventBridge からの実行権限を付与
echo "[3/4] Step Functions の実行ロールを確認..."
STATE_MACHINE_ROLE_ARN=$(aws stepfunctions describe-state-machine \
  --state-machine-arn "$STATE_MACHINE_ARN" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query 'roleArn' \
  --output text)

echo "State Machine Role: $STATE_MACHINE_ROLE_ARN"

# EventBridge が Step Functions を起動できるように IAM ロールを作成
EVENTBRIDGE_ROLE_NAME="keywords-checker-eventbridge-role"

# ロールが既に存在するか確認
if aws iam get-role --role-name "$EVENTBRIDGE_ROLE_NAME" --profile "$PROFILE" 2>/dev/null; then
  echo "✅ EventBridge ロールは既に存在します"
else
  echo "EventBridge ロールを作成中..."
  aws iam create-role \
    --role-name "$EVENTBRIDGE_ROLE_NAME" \
    --assume-role-policy-document '{
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
    }' \
    --profile "$PROFILE" \
    --region "$REGION"
  
  # Step Functions 実行権限をアタッチ
  aws iam put-role-policy \
    --role-name "$EVENTBRIDGE_ROLE_NAME" \
    --policy-name "StepFunctionsExecutionPolicy" \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": "states:StartExecution",
          "Resource": "'"$STATE_MACHINE_ARN"'"
        }
      ]
    }' \
    --profile "$PROFILE" \
    --region "$REGION"
  
  echo "✅ EventBridge ロールが作成されました"
fi

EVENTBRIDGE_ROLE_ARN="arn:aws:iam::730335237698:role/$EVENTBRIDGE_ROLE_NAME"
echo ""

# Step 4: EventBridge Rule のターゲットに Step Functions を設定
echo "[4/4] EventBridge Rule のターゲットに Step Functions を設定..."
aws events put-targets \
  --rule "$RULE_NAME" \
  --targets '[
    {
      "Id": "1",
      "Arn": "'"$STATE_MACHINE_ARN"'",
      "RoleArn": "'"$EVENTBRIDGE_ROLE_ARN"'",
      "InputTransformer": {
        "InputPathsMap": {
          "bucket": "$.detail.bucket.name",
          "key": "$.detail.object.key"
        },
        "InputTemplate": "{\"bucket\": <bucket>, \"key\": <key>}"
      }
    }
  ]' \
  --profile "$PROFILE" \
  --region "$REGION"

echo "✅ EventBridge Rule のターゲットが設定されました"
echo ""

# 設定確認
echo "=== 設定確認 ==="
echo "Rule Name: $RULE_NAME"
echo "Rule ARN: $RULE_ARN"
echo "EventBridge Role: $EVENTBRIDGE_ROLE_ARN"
echo "State Machine: $STATE_MACHINE_ARN"
echo ""
echo "✅ EventBridge のセットアップが完了しました！"
echo ""
echo "【テスト方法】"
echo "以下のコマンドで Excel ファイルを input/ フォルダにアップロードすると、"
echo "Step Functions が自動的に起動します："
echo ""
echo "  aws s3 cp sandbox_test.xlsm s3://$BUCKET_NAME/input/test.xlsx --profile $PROFILE"
echo ""
