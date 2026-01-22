# クイックスタートガイド

Keywords Checkerを素早く起動するためのガイドです。

## 🚀 30秒で起動

### 1. API Keyの設定

```bash
cd backend
cp .env.example .env
# エディタで .env を開いて OPENAI_API_KEY を設定
# LITELLM_API_BASE と LITELLM_MODEL も必要に応じて設定
```

### 2. 依存パッケージのインストール

**macOS/Linux:**
```bash
# 仮想環境を作成（推奨）
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# パッケージをインストール（仮想環境内）
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. サーバー起動

**ターミナル 1 (バックエンド):**
```bash
cd backend
python app.py
```

**ターミナル 2 (フロントエンド):**
```bash
cd frontend
python -m http.server 8080
```

### 4. ブラウザでアクセス

```
http://localhost:8080
```

## 📝 テスト

### 単一チェックのテスト

商品情報に以下を入力:

```
商品名: テストマスク
キャッチコピー: 安心の日本製マスク
説明: ウイルス予防に効果的
管理カテゴリー大: 衛生用品
管理カテゴリー中: マスク
```

→ 「チェック実行」をクリック

期待結果: NG判定（「安心」「予防」「効果」などのキーワード違反）

### Excel一括チェックのテスト

`examples/sample_products.xlsx` ファイルを使用してテスト可能です。

## 🔧 よくある問題

### Q: `ModuleNotFoundError: No module named 'anthropic'`

A: 依存パッケージをインストール:
```bash
cd backend
pip install -r requirements.txt
```

### Q: `API key not found`

A: `.env` ファイルにAPI Keyを設定:
```bash
cd backend
cat .env  # 内容確認
# ANTHROPIC_API_KEY=sk-ant-... が設定されているか確認
```

### Q: フロントエンドが表示されない

A: 正しいURLでアクセスしているか確認:
```
http://localhost:8080/index.html
```

### Q: CORSエラー

A: バックエンドが起動しているか確認:
```bash
curl http://localhost:5000/api/health
# {"status":"healthy","skills_loaded":1} が返ることを確認
```

## 📚 詳細情報

- [セットアップガイド](SETUP.md) - 詳細なセットアップ手順
- [README.md](../README.md) - プロジェクト概要とAPI仕様

## 🎯 次のステップ

1. カスタムリファレンスファイルの追加
2. 新しいスキルの作成
3. フロントエンドのカスタマイズ

Happy Checking! 🎉
