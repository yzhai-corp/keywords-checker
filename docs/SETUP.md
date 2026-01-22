# セットアップガイド

このドキュメントでは、Keywords Checkerのセットアップ手順を説明します。

## 前提条件

- Python 3.10以上がインストールされていること
- LiteLLM API Key

## セットアップ手順

### 1. リポジトリのクローン

```bash
cd /path/to/your/workspace
git clone <repository-url>
cd keywords-checker
```

### 2. バックエンドのセットアップ

#### 2.1 仮想環境の作成（推奨）

**macOS/Linux:**
```bash
cd backend

# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# 成功すると、プロンプトの先頭に (venv) が表示されます
```

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

#### 2.2 依存パッケージのインストール

**仮想環境が有効な状態で:**
```bash
# 仮想環境内では pip が使えます
pip install -r requirements.txt
```

**仮想環境を使わない場合（非推奨）:**
```bash
# macOS/Linux
pip3 install -r requirements.txt

# または
python3 -m pip install -r requirements.txt
```

#### 2.3 環境変数の設定

```bash
# .envファイルを作成
cp .env.example .env

# .envファイルを編集してAPI Keyを設定
# ANTHROPIC_API_KEY=your_actual_api_key_here
```

エディタで `.env` ファイルを開き、以下のように編集:

```env
OPENAI_API_KEY=sk-xxxxxx
LITELLM_API_BASE=https://askul-gpt.askul-it.com/v1
LITELLM_MODEL=gpt-5-mini
```

### 3. フロントエンドの準備

フロントエンドは静的ファイルなので、特別なセットアップは不要です。

### 4. サーバーの起動

#### 4.1 バックエンドサーバーの起動

```bash
cd backend
python app.py
```

正常に起動すると、以下のようなメッセージが表示されます:

```
Loaded skills:
  - 商品コピーチェック: チェック対象物をルール違反しているか確認するツールです。
 * Running on http://0.0.0.0:5000
```

#### 4.2 フロントエンドサーバーの起動

別のターミナルウィンドウを開いて:

```bash
cd frontend
python -m http.server 8080
```

または、シンプルに:

```bash
# macOS
open frontend/index.html

# Linux
xdg-open frontend/index.html

# Windows
start frontend/index.html
```

### 5. 動作確認

1. ブラウザで `http://localhost:8080` を開く
2. 「単一チェック」タブで以下のテスト入力を試す:

```
商品名: テスト商品
キャッチコピー: 安心の日本製マスク
```

3. 「チェック実行」ボタンをクリック
4. 結果が表示されることを確認

### 6. Excel一括チェックのテスト

1. サンプルExcelファイルを作成（以下の列を含む）:
   - 商品名
   - キャッチコピー
   - 説明

2. 「一括チェック (Excel)」タブを選択
3. ファイルをアップロード
4. 「一括チェック実行」をクリック
5. 結果ファイルがダウンロードされることを確認

## トラブルシューティング

### エラー: `pip: command not found` (macOS)

macOSでは`pip3`または`python3 -m pip`を使用してください:

```bash
# 方法1: pip3を使用
pip3 install -r requirements.txt

# 方法2: python3 -m pipを使用
python3 -m pip install -r requirements.txt

# 方法3: 仮想環境を使用（推奨）
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # 仮想環境内ではpipが使えます
```

### エラー: `ModuleNotFoundError: No module named 'xxx'`

依存パッケージが不足しています:

```bash
cd backend

# 仮想環境が有効な場合
pip install -r requirements.txt

# 仮想環境を使用していない場合（macOS）
pip3 install -r requirements.txt
```

### エラー: `API key not found`

`.env` ファイルが正しく設定されていません:

```bash
cd backend
# .envファイルを確認
cat .env

# API Keyが設定されているか確認
# 設定されていない場合は編集
nano .env  # または vi .env
```

### エラー: `Skills directory not found`

スキルファイルがコピーされていません:

```bash
# .github/skills から backend/skills にコピー
cp -r .github/skills/商品コピーチェック backend/skills/
```

### CORS エラー

バックエンドサーバーが起動していることを確認:

```bash
# ヘルスチェック
curl http://localhost:5000/api/health
```

### ポートが既に使用されている

別のポートを使用:

```bash
# バックエンド
cd backend
python app.py  # コード内のポート番号を変更

# フロントエンド
cd frontend
python -m http.server 8081  # 別のポート番号
```

## 次のステップ

- [README.md](../README.md) でAPIの詳細を確認
- カスタムスキルの作成
- 新しいリファレンスファイルの追加

## サポート

問題が解決しない場合は、開発チームまでお問い合わせください。
