# システムシーケンス図

## Excel一括チェック処理フロー

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Browser as ブラウザ
    participant Flask as Flask Backend
    participant SkillMgr as Skill Manager
    participant Memory as メモリ (Skills)
    participant LLM as LLM API

    Note over User,LLM: サーバー起動時（1回のみ）
    Flask->>SkillMgr: load_all_skills()
    activate SkillMgr
    SkillMgr->>Memory: Load SKILL.md
    SkillMgr->>Memory: Load references/*.md (200+個)
    Memory-->>SkillMgr: 全スキル・参照データ
    deactivate SkillMgr
    
    Note over User,LLM: Excel一括チェック処理
    User->>Browser: Excelファイルを選択
    User->>Browser: 「一括チェック実行」クリック
    Browser->>Flask: POST /api/check-excel (multipart/form-data)
    activate Flask
    
    Flask->>Flask: Excelファイル受信
    Flask->>Flask: シート「チェック対象」を読み込み (pandas)
    Flask->>Flask: 列「*商品名」存在確認
    Flask->>Flask: 全列を文字列型として読み込み
    
    Note over Flask,LLM: 各行をループ処理
    loop 各行 (1商品ごと)
        Flask->>Flask: build_product_message(row)
        Note right of Flask: チェック対象列のみ抽出:<br/>*変更前_商品の特徴BtoB<br/>*変更前_MDおすすめコメントBtoB<br/>*変更前_短いキャッチコピーBtoB<br/>*変更前_キャッチコピーBtoC<br/>*変更前_商品の特徴BtoC
        
        Flask->>SkillMgr: detect_keywords(product_message)
        activate SkillMgr
        Note right of SkillMgr: 正規表現で単語境界を考慮した<br/>部分一致検索
        SkillMgr->>Memory: 商品テキスト内のキーワード検出
        Memory-->>SkillMgr: 検出されたキーワードリスト
        deactivate SkillMgr
        
        Flask->>Flask: Log: 検出されたキーワード数
        Flask->>Flask: Log: 使用するreferencesファイル
        
        Flask->>SkillMgr: build_dynamic_system_prompt(detected_keywords)
        activate SkillMgr
        Note right of SkillMgr: SKILL.md +<br/>検出されたキーワードの<br/>referencesのみ結合
        SkillMgr->>Memory: SKILL.md取得
        SkillMgr->>Memory: 検出されたreferences/*.md取得
        Memory-->>SkillMgr: 動的system_prompt
        deactivate SkillMgr
        
        Flask->>LLM: litellm.completion(system_prompt, product_message)
        activate LLM
        Note right of LLM: model: gpt-5-mini<br/>max_tokens: 4096<br/>timeout: 120秒<br/>num_retries: 2
        LLM-->>Flask: チェック結果 (OK/NG/コメント)
        deactivate LLM
        
        Flask->>Flask: extract_conclusion(result_text)
        Flask->>Flask: results.append(), conclusions.append()
    end
    
    Flask->>Flask: df['チェック結果'] = results (文字列型)
    Flask->>Flask: df['結論'] = conclusions (文字列型)
    Flask->>Flask: Create Excel in memory (BytesIO)
    Flask-->>Browser: send_file (check_result.xlsx)
    deactivate Flask
    
    Browser->>User: Excelファイルダウンロード
```

## 主な処理ポイント

### 1. **サーバー起動時の初期化**
- 全SKILL.mdと200+個のreferences/*.mdをメモリに読み込み
- 以降、ファイルI/Oは発生しない

### 2. **動的キーワード検出**
- 商品テキストから正規表現で単語境界を考慮してキーワード検出
- 検出されたキーワードのreferencesのみをLLMに送信

### 3. **トークン最適化**
- **改善前**: 全references (200+個) × 行数
- **改善後**: 検出されたreferences (平均5-10個) × 行数
- **削減率**: 約95-98%

### 4. **データ型保持**
- 入力Excelの全列を文字列型として読み込み
- 出力列も明示的に文字列型で追加
- タスクIDの先頭0や日付フォーマットが保持される

### 5. **エラーハンドリング**
- LLM APIリトライ: 最大2回
- タイムアウト: 120秒/リクエスト
- 処理中断を防ぐため自動再起動を無効化 (use_reloader=False)

## ログ出力例

```
2026-01-26 14:30:15 - INFO - 📊 Excel一括チェック開始: 100行 (ファイル: products.xlsx)
2026-01-26 14:30:15 - INFO - 進捗: 1/100 行処理中...
2026-01-26 14:30:15 - INFO - 行 1: 検出されたキーワード数 = 3
2026-01-26 14:30:15 - INFO -   → 使用するreferencesファイル: 免疫, 効果, 美白
2026-01-26 14:30:25 - INFO - 行 2: 検出されたキーワード数 = 5
2026-01-26 14:30:25 - INFO -   → 使用するreferencesファイル: 薬, 治療, 改善, 効果, 機能性を
2026-01-26 14:30:35 - INFO - 行 3: キーワード検出なし（一般的なチェックのみ実施）
...
2026-01-26 14:45:00 - INFO - ✅ 処理完了: 100行
```
