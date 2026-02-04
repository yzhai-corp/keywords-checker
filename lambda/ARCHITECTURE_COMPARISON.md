# アーキテクチャ比較と推奨構成

## 要件

- **処理量**: 10,000行のExcelデータ
- **制限時間**: 15分以内
- **1行あたりの処理時間**: LLM API呼び出しで約30秒（推定）
- **必要な並列度**: 10,000行 × 30秒 ÷ (15分 × 60秒) = **約333並列**
- **安全マージン**: 400-500並列を推奨

## 構成案の比較

### 案1: Lambda → Lambda 直接呼び出し（現在の実装）

```
S3 → Lambda1 → Lambda2 (×並列) → Lambda1 → S3
```

#### メリット
- シンプルな構成
- デプロイが簡単

#### デメリット
❌ **Lambda1が15分のタイムアウト制限に到達する可能性が高い**
- Lambda1がすべてのLambda2の完了を同期的に待つ必要がある
- 10,000行を処理する場合、最も遅いLambda2が完了するまで待機

❌ **同時実行数の管理が難しい**
- Lambda1から一度に数千のLambda2を呼び出すとスロットリングのリスク

❌ **エラーハンドリングが複雑**
- 一部のLambda2が失敗した場合の再処理が困難

❌ **コスト効率が悪い**
- Lambda1が待機している間もコストが発生

#### 結論
**推奨しません** - 大規模バッチ処理には不向き

---

### 案2: Step Functions + Lambda（推奨✅）

```
S3 → Lambda (Splitter) → Step Functions (Map State) → Lambda (Processor) ×並列 → Lambda (Combiner) → S3
```

#### アーキテクチャ詳細

1. **Lambda Splitter**: Excelを読み込み、行データの配列を作成
2. **Step Functions Map State**: 各行を並列処理（最大10,000並列）
3. **Lambda Processor**: 1行ずつLLM APIを呼び出し
4. **Lambda Combiner**: 結果を統合してExcelを作成

#### メリット
✅ **15分の制限を超えられる**
- Step Functionsは最大1年間実行可能

✅ **自動的な並列度制御**
- Map Stateが自動で並列実行を管理

✅ **優れたエラーハンドリング**
- 個別のタスクの失敗を検出して再試行可能
- 失敗した行のみを再処理できる

✅ **視覚的なモニタリング**
- Step Functionsコンソールで進捗を確認できる

✅ **コスト最適化**
- 待機時間のコストがかからない

#### デメリット
⚠️ **追加の設定が必要**
- Step Functions定義が必要

⚠️ **Step Functionsの制限**
- 実行履歴は最大25,000イベント（大規模な場合は分割が必要）

#### コスト見積もり（月100回実行の場合）
- Step Functions: $0.025 × 10,000ステート遷移 × 100回 = **$25/月**
- Lambda Processor: 1GB × 30秒 × 10,000行 × 100回 = **$50/月**
- 合計: 約**$75/月**

---

### 案3: SQS + Lambda（非同期処理）

```
S3 → Lambda (Publisher) → SQS → Lambda (Consumer) ×並列 → DynamoDB → Lambda (Combiner) → S3
```

#### アーキテクチャ詳細

1. **Lambda Publisher**: Excelを読み込み、各行をSQSにメッセージとして送信
2. **SQS**: メッセージキュー（標準キュー）
3. **Lambda Consumer**: SQSイベントトリガーで起動、LLM APIを呼び出し、結果をDynamoDBに保存
4. **Lambda Combiner**: すべての処理完了後、DynamoDBから結果を取得してExcel作成

#### メリット
✅ **スケーラブル**
- SQSが自動的にメッセージを分散

✅ **耐障害性が高い**
- メッセージが失われない（Dead Letter Queue対応）

✅ **デカップリング**
- 各コンポーネントが独立

#### デメリット
⚠️ **複雑な完了検知**
- すべての処理が完了したことを検知する仕組みが必要

⚠️ **DynamoDBのコスト**
- 一時的に10,000件のデータを保存

⚠️ **順序保証がない**
- 標準キューでは処理順序が保証されない

---

### 案4: EventBridge Scheduler + Lambda

```
S3 → Lambda (Scheduler) → EventBridge Scheduler → Lambda (Processor) ×並列 → S3 + DynamoDB
```

#### メリット
✅ **料金が安い**
- EventBridge Schedulerは低コスト

#### デメリット
❌ **スケジュール数の制限**
- アカウントあたり最大100万スケジュール

❌ **完了検知が複雑**

---

## 推奨構成: Step Functions + Lambda

### 理由

1. **確実に15分以内で処理可能**（Step Functionsの実行時間制限は1年）
2. **並列度の自動管理**（Map Stateで最大10,000並列）
3. **優れた可視性**（進捗とエラーを視覚的に確認）
4. **シンプルな実装**（エラーハンドリングが組み込み済み）
5. **適切なコスト**（待機時間のコストなし）

### 必要な同時実行数の計算

```
必要な並列度 = 総処理時間 / 制限時間
              = (10,000行 × 30秒/行) / (15分 × 60秒)
              = 300,000秒 / 900秒
              = 333並列

安全マージンを考慮: 400-500並列を設定
```

### Lambda設定

- **Lambda Processor**:
  - メモリ: 1024 MB
  - タイムアウト: 2分
  - 予約済み同時実行数: 500

- **Lambda Splitter**:
  - メモリ: 2048 MB
  - タイムアウト: 5分

- **Lambda Combiner**:
  - メモリ: 2048 MB
  - タイムアウト: 10分

---

## Step Functions実装例

### State Machine定義（JSON）

```json
{
  "Comment": "Keywords Checker Parallel Processing",
  "StartAt": "SplitExcel",
  "States": {
    "SplitExcel": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:keywords-checker-splitter",
      "Next": "ProcessRows"
    },
    "ProcessRows": {
      "Type": "Map",
      "ItemsPath": "$.rows",
      "MaxConcurrency": 500,
      "Iterator": {
        "StartAt": "ProcessRow",
        "States": {
          "ProcessRow": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:keywords-checker-processor",
            "Retry": [
              {
                "ErrorEquals": ["States.TaskFailed"],
                "IntervalSeconds": 2,
                "MaxAttempts": 3,
                "BackoffRate": 2
              }
            ],
            "End": true
          }
        }
      },
      "ResultPath": "$.results",
      "Next": "CombineResults"
    },
    "CombineResults": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:keywords-checker-combiner",
      "End": true
    }
  }
}
```

---

## 次のステップ

Step Functions構成に切り替える場合は、以下の3つのLambda関数を実装します：

1. **Splitter**: Excelを行データの配列に分割
2. **Processor**: 1行をLLM APIでチェック（現在のLambda2相当）
3. **Combiner**: 結果を統合してExcelを作成

実装しますか？


## AIからの回答1
良い質問です！Lambda-to-Lambdaの構成には課題があります。より良い構成を提案させてください。 

Read [](file:///Users/abi01711/workspace/keywords-checker/lambda/DEPLOY.md#1-1), lines 1 to 50

Created [](file:///Users/abi01711/workspace/keywords-checker/lambda/ARCHITECTURE_COMPARISON.md)

詳細な比較ドキュメントを作成しました。**要点をまとめます**：

## Lambda→Lambda呼び出しの問題点

❌ **15分のタイムアウトリスク**
- Lambda1が10,000個のLambda2の完了を待つ必要がある
- 最も遅い処理が完了するまでLambda1が待機

❌ **必要な並列数: 400-500並列**
```
計算式：10,000行 × 30秒/行 ÷ (15分 × 60秒) = 333並列
安全マージン込みで 400-500並列
```

❌ **エラーハンドリングが困難**
- 一部失敗時の再処理が複雑

## 推奨構成: Step Functions + Lambda ✅

```
S3 
  ↓
Lambda Splitter (Excelを行配列に分割)
  ↓
Step Functions Map State (自動並列実行)
  ├→ Lambda Processor (LLM API) ×500並列
  ├→ Lambda Processor (LLM API)
  └→ Lambda Processor (LLM API)
  ↓
Lambda Combiner (結果統合→Excel作成)
  ↓
S3
```

### メリット

✅ **15分制限なし**（Step Functionsは最大1年実行可能）
✅ **自動並列管理**（Map Stateで最大10,000並列）
✅ **視覚的モニタリング**（進捗が見える）
✅ **優れたエラーハンドリング**（自動リトライ）
✅ **コスト効率**（月$75程度）

### 次のアクション

Step Functions構成を実装しますか？必要なのは：

1. Lambda Splitter（Excel分割）
2. Lambda Processor（現Lambda2を改修）
3. Lambda Combiner（結果統合）
4. Step Functions定義

実装しましょうか？

Made changes.


## AIからの回答2
ARCHITECTURE_COMPARISON.mdの4つの構成案について詳しく説明します！

## 📊 4つのアーキテクチャ構成案

---

## 🔴 案1: Lambda → Lambda 直接呼び出し（現在の実装）

### アーキテクチャ
```
S3 → Lambda1 → Lambda2 (×並列) → Lambda1 → S3
```

### 動作フロー
1. S3にExcelファイルがアップロードされる
2. **Lambda1**がトリガーされ、Excelを読み込む
3. Lambda1が各行について**Lambda2を同期的に呼び出し**（InvokeFunction）
4. Lambda1はすべてのLambda2の**完了を待つ**
5. Lambda1が結果を統合してExcelを作成
6. S3にアップロード

### メリット ✅
- シンプルで理解しやすい
- デプロイが簡単（Lambda関数2つだけ）
- 追加のAWSサービス不要

### デメリット ❌
- **Lambda1が15分でタイムアウト**する可能性が高い
  - 10,000行 × 30秒/行 = 300,000秒（83時間相当）
  - 並列実行しても、最も遅いLambda2を待つ必要がある
- **同時実行数の管理が難しい**
  - 一度に数千のLambda2を呼び出すとスロットリング
- **エラーハンドリングが複雑**
  - 一部失敗時の再処理が困難
- **コスト効率が悪い**
  - Lambda1が待機中もコスト発生

### 結論
✅ **小規模データ（数百行）なら問題なし**（今回の検証でも動作しました）
❌ **大規模データ（数千〜1万行）には不向き**

---

## 🟢 案2: Step Functions + Lambda（推奨✅）

### アーキテクチャ
```
S3 → Lambda Splitter → Step Functions (Map State) → Lambda Processor ×並列 → Lambda Combiner → S3
```

### 動作フロー
1. S3にExcelファイルがアップロードされる
2. **Lambda Splitter**がトリガーされ、Excelを読み込み
3. Splitterが行データを**配列**に変換してStep Functionsに渡す
4. **Step Functions Map State**が各行を**自動的に並列処理**
   - 最大10,000並列まで対応
   - 並列度を制御可能（例: 500並列）
5. **Lambda Processor**が各行を処理（LLM API呼び出し）
6. すべての処理完了後、**Lambda Combiner**が結果を統合
7. Excelファイルを作成してS3にアップロード

### メリット ✅
- **15分制限なし**（Step Functionsは最大1年実行可能）
- **自動並列管理**（Map Stateが並列実行を制御）
- **優れたエラーハンドリング**
  - 個別タスクの失敗を検出
  - 自動リトライ設定可能
  - 失敗した行だけ再処理可能
- **視覚的モニタリング**
  - Step Functionsコンソールで進捗確認
  - どの行が処理中/完了/失敗かが一目瞭然
- **コスト最適化**
  - 待機時間のコストなし

### デメリット ⚠️
- Step Functions定義が必要（JSON）
- Lambda関数が3つ必要（Splitter, Processor, Combiner）
- Step Functionsの実行履歴制限（25,000イベント）
  - 超大規模なら分割処理が必要

### コスト見積もり（月100回実行）
- Step Functions: $25/月
- Lambda: $50/月
- **合計: 約$75/月**

### 結論
✅ **大規模バッチ処理に最適**
✅ **信頼性とモニタリングが重要な場合に推奨**

---

## 🟡 案3: SQS + Lambda（非同期処理）

### アーキテクチャ
```
S3 → Lambda Publisher → SQS → Lambda Consumer ×並列 → DynamoDB → Lambda Combiner → S3
```

### 動作フロー
1. S3にExcelファイルがアップロードされる
2. **Lambda Publisher**がExcelを読み込む
3. 各行を**SQSメッセージ**として送信（10,000メッセージ）
4. **Lambda Consumer**がSQSから自動的にトリガーされる
   - SQSが自動的にメッセージを分散
   - Lambda同時実行数に応じて並列処理
5. Consumerが処理結果を**DynamoDB**に保存
6. すべて完了後、**Lambda Combiner**がDynamoDBから結果取得
7. Excelを作成してS3にアップロード

### メリット ✅
- **高いスケーラビリティ**（SQSが自動分散）
- **耐障害性**（メッセージが失われない）
- **デカップリング**（各コンポーネントが独立）
- **Dead Letter Queue対応**（失敗メッセージの管理）

### デメリット ⚠️
- **完了検知が複雑**
  - 10,000メッセージすべて完了したか判定が必要
  - CloudWatch EventやLambda内でカウンター管理が必要
- **DynamoDBコスト**
  - 一時的に10,000件保存
- **処理順序が保証されない**（標準キュー）

### 結論
✅ **非同期処理が必要な場合に適している**
⚠️ **完了検知の実装が複雑**

---

## 🔵 案4: EventBridge Scheduler + Lambda

### アーキテクチャ
```
S3 → Lambda Scheduler → EventBridge Scheduler → Lambda Processor ×並列 → S3 + DynamoDB
```

### 動作フロー
1. S3にExcelファイルがアップロードされる
2. **Lambda Scheduler**がExcelを読み込む
3. 各行に対してEventBridge Schedulerで**スケジュール作成**
4. スケジュールされたタイミングで**Lambda Processor**が実行
5. 結果をDynamoDBに保存
6. 完了後、Combinerが統合

### メリット ✅
- **低コスト**（EventBridge Schedulerは安価）
- **柔軟なスケジューリング**

### デメリット ❌
- **スケジュール数制限**（アカウントあたり100万まで）
- **即時処理には不向き**
- **完了検知が複雑**

### 結論
❌ **リアルタイム処理には不向き**

---

## 📋 比較表

| 項目 | 案1: Lambda→Lambda | 案2: Step Functions | 案3: SQS | 案4: EventBridge |
|------|-------------------|-------------------|----------|------------------|
| **実装の簡単さ** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **大規模処理** | ❌ | ✅ | ✅ | ⚠️ |
| **モニタリング** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **エラーハンドリング** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **コスト** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **リアルタイム性** | ✅ | ✅ | ✅ | ❌ |

---

## 🎯 推奨: Step Functions + Lambda（案2）

### 理由
1. **15分制限を超えられる**（最大1年実行可能）
2. **並列度の自動管理**（Map Stateで500並列設定可能）
3. **視覚的な進捗確認**（Step Functionsコンソール）
4. **優れたエラーハンドリング**（自動リトライ、失敗行のみ再処理）
5. **適切なコスト**（月$75程度）

---

質問があればどうぞ！どの構成が良いか、またはStep Functions実装を進めるか教えてください。