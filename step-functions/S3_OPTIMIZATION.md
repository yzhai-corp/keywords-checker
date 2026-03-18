# S3最適化版への変更サマリー

## 変更の背景

### 問題
- Step Functionsの256KB制限により、10,000行のデータを処理できない
- 現在の実装では行データ全体を配列として渡している（数MB）
- 1行が100バイトとしても、10,000行 × 100バイト = 1MB（256KB超過）

### 解決策
S3経由のデータ受け渡し方式に変更：
- Splitter: 行データをS3に個別保存、S3キーのリストのみを返す
- Processor: S3から行データを読み込んで処理
- State Machine: S3キーのリスト（数KB）を処理

## 変更されたファイル

### 1. splitter/lambda_function.py

#### 変更内容
- `save_rows_to_s3()` 関数を追加
- 各行データを `results/{execution_id}/rows/row_{index}.json` として保存
- 出力を `rows` から `s3_row_keys` に変更

#### 変更前
```python
result = {
    'execution_id': execution_id,
    'total_rows': total_rows,
    'rows': rows_data  # 行データ本体（数MB）
}
```

#### 変更後
```python
# 行データをS3に保存
s3_keys = save_rows_to_s3(bucket, execution_id, rows_data)

result = {
    'execution_id': execution_id,
    'total_rows': total_rows,
    's3_row_keys': s3_keys  # S3キーのリストのみ（数KB）
}
```

### 2. processor/lambda_function.py

#### 変更内容
- `load_row_data_from_s3()` 関数を追加
- lambda_handlerの入力パラメータを変更
- 行データをS3から読み込むように修正

#### 変更前
```python
def lambda_handler(event, context):
    execution_id = event.get('execution_id')
    row_index = event.get('row_index')
    row_data = event.get('row_data', {})  # 行データを直接受け取る
```

#### 変更後
```python
def lambda_handler(event, context):
    execution_id = event.get('execution_id')
    row_index = event.get('row_index')
    s3_key = event.get('s3_key')
    bucket = event.get('bucket', RESULTS_BUCKET)
    
    # S3から行データを読み込み
    row_data = load_row_data_from_s3(bucket, s3_key)
```

### 3. state-machine.json

#### 変更内容
- Map StateのItemsPathを変更
- Parametersを変更（row_data → s3_key, bucket）

#### 変更前
```json
"ProcessRows": {
  "Type": "Map",
  "ItemsPath": "$.rows",
  "Parameters": {
    "execution_id.$": "$.execution_id",
    "row_index.$": "$$.Map.Item.Value.row_index",
    "row_data.$": "$$.Map.Item.Value"
  }
}
```

#### 変更後
```json
"ProcessRows": {
  "Type": "Map",
  "ItemsPath": "$.s3_row_keys",
  "Parameters": {
    "execution_id.$": "$.execution_id",
    "row_index.$": "$$.Map.Item.Value.row_index",
    "s3_key.$": "$$.Map.Item.Value.s3_key",
    "bucket.$": "$$.Map.Item.Value.bucket"
  }
}
```

### 4. タイムアウト設定

- Processorのタイムアウト: 120秒 → **90秒**（LLM API: 70秒 + マージン）
- DEPLOY.mdを更新

## データフロー比較

### 変更前（256KB制限に抵触）
```
Splitter
  ↓ [行データ配列: 数MB]
Map State (256KB制限超過エラー)
  ↓
Processor
```

### 変更後（S3経由）
```
Splitter
  ↓ 各行をS3に保存
  ↓ [S3キーのリスト: 数KB]
Map State (OK)
  ↓ [S3キー: 数百バイト]
Processor
  ↓ S3から行データ読み込み
  ↓ 処理
```

## 処理時間の見積もり

### 10,000行の場合

| 項目 | 値 |
|------|-----|
| データ行数 | 10,000行 |
| LLM API処理時間 | 70秒/行 |
| 並列処理数 | 500 |
| 総バッチ数 | 20 |
| Map State処理時間 | 1,400秒（23.3分） |
| Splitter処理時間 | 10-20秒 |
| Combiner処理時間 | 60-120秒 |
| **合計処理時間** | **約25-27分** |

## デプロイ方法

### 自動デプロイ（推奨）

```bash
cd /Users/abi01711/workspace/keywords-checker/step-functions
chmod +x deploy-s3-optimized.sh
./deploy-s3-optimized.sh
```

### 手動デプロイ

1. **Splitterを更新**
```bash
cd splitter
zip -r lambda.zip lambda_function.py
aws s3 cp lambda.zip s3://BUCKET/lambda-code/splitter.zip --region ap-northeast-1
aws lambda update-function-code \
  --function-name keywords-checker-splitter \
  --s3-bucket BUCKET \
  --s3-key lambda-code/splitter.zip \
  --region ap-northeast-1
```

2. **Processorを更新**
```bash
cd processor
zip -r lambda.zip lambda_function.py
aws s3 cp lambda.zip s3://BUCKET/lambda-code/processor.zip --region ap-northeast-1
aws lambda update-function-code \
  --function-name keywords-checker-processor \
  --s3-bucket BUCKET \
  --s3-key lambda-code/processor.zip \
  --region ap-northeast-1

aws lambda update-function-configuration \
  --function-name keywords-checker-processor \
  --timeout 90 \
  --region ap-northeast-1
```

3. **State Machineを更新**
```bash
cd ..
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:REGION:ACCOUNT:stateMachine:keywords-checker-state-machine \
  --definition file://state-machine.json \
  --region ap-northeast-1
```

## テスト方法

```bash
# 10,000行のテストファイルをアップロード
aws s3 cp test_10000.xlsx s3://BUCKET/input/ --region ap-northeast-1

# Step Functionsコンソールで実行状況を確認
# 約25-27分後、output/にExcelファイルが生成される
```

## メリット

✅ **256KB制限を回避**: S3経由でデータを受け渡すため、行数制限なし
✅ **10,000行以上対応**: 実行履歴イベント制限（25,000イベント）まで処理可能
✅ **スケーラブル**: 並列数を増やせば、さらに高速化可能
✅ **コスト効率**: S3ストレージコストは微小（数MB）

## 次のステップ

1. **デプロイ**: `deploy-s3-optimized.sh` を実行
2. **テスト**: 131行のテストファイルで動作確認
3. **大規模テスト**: 1,000行、5,000行、10,000行で段階的にテスト
4. **Production Mode**: VPC設定とLiteLLM API統合
