#!/bin/bash

# S3経由データ受け渡し方式へのデプロイスクリプト
# 10,000行対応のための256KB制限回避

set -e

REGION="ap-northeast-1"
ACCOUNT_ID="902163356275"
BUCKET="askul-sandbox-01-regulation-step-functions-bucket"
STATE_MACHINE_NAME="keywords-checker-state-machine"
STATE_MACHINE_ARN="arn:aws:states:${REGION}:${ACCOUNT_ID}:stateMachine:${STATE_MACHINE_NAME}"

echo "========================================"
echo "S3最適化版デプロイ開始"
echo "========================================"

# Step 1: Splitterの更新
echo ""
echo "[1/4] Splitter Lambda関数を更新中..."
cd /Users/abi01711/workspace/keywords-checker/step-functions/splitter

# 既存のzipファイルを削除
rm -f lambda.zip

# Lambda関数をパッケージ化
zip -r lambda.zip lambda_function.py

# S3にアップロード
aws s3 cp lambda.zip s3://${BUCKET}/lambda-code/splitter.zip --region ${REGION}

# Lambda関数コードを更新
aws lambda update-function-code \
  --function-name keywords-checker-splitter \
  --s3-bucket ${BUCKET} \
  --s3-key lambda-code/splitter.zip \
  --region ${REGION}

echo "✅ Splitter更新完了"

# Step 2: Processorの更新
echo ""
echo "[2/4] Processor Lambda関数を更新中..."
cd /Users/abi01711/workspace/keywords-checker/step-functions/processor

# 既存のzipファイルを削除
rm -f lambda.zip

# Lambda関数をパッケージ化
zip -r lambda.zip lambda_function.py

# S3にアップロード
aws s3 cp lambda.zip s3://${BUCKET}/lambda-code/processor.zip --region ${REGION}

# Lambda関数コードを更新
aws lambda update-function-code \
  --function-name keywords-checker-processor \
  --s3-bucket ${BUCKET} \
  --s3-key lambda-code/processor.zip \
  --region ${REGION}

# タイムアウトを90秒に更新
aws lambda update-function-configuration \
  --function-name keywords-checker-processor \
  --timeout 90 \
  --region ${REGION}

echo "✅ Processor更新完了（タイムアウト: 90秒）"

# Step 3: State Machineの更新
echo ""
echo "[3/4] Step Functions State Machineを更新中..."
cd /Users/abi01711/workspace/keywords-checker/step-functions

# State Machine定義を更新
aws stepfunctions update-state-machine \
  --state-machine-arn ${STATE_MACHINE_ARN} \
  --definition file://state-machine.json \
  --region ${REGION}

echo "✅ State Machine更新完了"

# Step 4: 変更の反映を待つ
echo ""
echo "[4/4] 変更の反映を待機中..."
sleep 5

echo ""
echo "========================================"
echo "✅ デプロイ完了"
echo "========================================"
echo ""
echo "変更内容："
echo "  - Splitter: 行データをS3に保存（results/{execution_id}/rows/row_{index}.json）"
echo "  - Processor: S3から行データを読み込み（タイムアウト90秒）"
echo "  - State Machine: S3キーのリストを処理"
echo ""
echo "これにより10,000行以上の処理が可能になりました。"
echo ""
echo "テスト方法："
echo "  aws s3 cp examples/test.xlsx s3://${BUCKET}/input/ --region ${REGION}"
echo ""
