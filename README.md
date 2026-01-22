# Keywords Checker - 商品コピーチェッカー

商品キャッチコピーに対し、薬機法・景表法に基づいた要注意表現のワードと照合し、違反となるコピー表現がないかをチェックするWebアプリケーション。

## 概要

このツールは、商品の広告・販促用コピー（テキスト）を薬機法・景表法などの関連法令および社内ルールに照らして、NG/注意表現を検出し、修正方針をコメントします。

### 主な機能

- **単一チェック**: 1つの商品情報を入力して即座にチェック
- **一括チェック**: Excelファイルをアップロードして複数商品を一括チェック
- **LiteLLM API活用**: 高精度なLLMを使用した判定（gpt-5-miniモデル）

## プロジェクト構造

```
keywords-checker/
├── README.md
├── .gitignore
│
├── backend/
│   ├── app.py                          # Flask server with Excel support
│   ├── skill_manager.py                # Skill loader and manager
│   ├── requirements.txt                # Python dependencies
│   ├── .env                            # API keys (not in git)
│   │
│   └── skills/                         # Skills directory
│       └── 商品コピーチェック/
│           ├── SKILL.md                # Main skill definition
│           └── references/             # Reference files (200+ keywords)
│
├── frontend/
│   ├── index.html                      # Web UI
│   ├── app.js                          # Frontend logic
│   └── style.css                       # Styling
│
└── .github/
    └── skills/                         # Original skill files
        └── 商品コピーチェック/
            ├── SKILL.md
            ├── references/
            ├── master.csv
            └── generate_references.py
```

## セットアップ

### 1. 必要な環境

- Python 3.10以上
- Node.js (フロントエンド開発時のみ)
- LiteLLM API Key

### 2. スキルファイルのコピー

```bash
# .github/skills から backend/skills にコピー
cp -r .github/skills/商品コピーチェック backend/skills/
```

### 3. バックエンドのセットアップ

```bash
cd backend

# 仮想環境の作成（推奨）
# macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# Windows:
# python -m venv venv
# venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してAPI Keyを設定
```

### 4. API Keyの取得と設定

1. LiteLLM API Keyを取得
2. `backend/.env` ファイルに以下を記載:

```env
OPENAI_API_KEY=sk-xxxxxx
LITELLM_API_BASE=https://askul-gpt.askul-it.com/v1
LITELLM_MODEL=gpt-5-mini
```

### 5. サーバーの起動

```bash
cd backend
python app.py
```

サーバーは `http://localhost:5001` で起動します。

### 6. フロントエンドの起動

別のターミナルで:

```bash
cd frontend
# 簡易的なHTTPサーバーを起動
python -m http.server 8080
```

ブラウザで `http://localhost:8080` にアクセスします。

## 使い方

### 単一チェック

1. ブラウザで `http://localhost:8080` を開く
2. 「単一チェック」タブを選択
3. 商品情報を入力（商品名、説明、キャッチコピーなど）
4. 「チェック実行」ボタンをクリック
5. 結果が表示されます（OK/NG + 詳細）

### 一括チェック (Excel)

1. 「一括チェック (Excel)」タブを選択
2. Excelファイルを準備（各行が1つの商品）
   - 列: 商品名、カタログ商品名、キャッチコピーなど
3. ファイルをアップロード
4. 「一括チェック実行」をクリック
5. 結果がExcelファイルでダウンロードされます

## APIエンドポイント

### `GET /api/health`
ヘルスチェック

### `GET /api/skills`
利用可能なスキルの一覧を取得

### `POST /api/check`
単一商品のチェック

**リクエスト:**
```json
{
  "skill_name": "商品コピーチェック",
  "product_info": "商品名: テスト商品\n説明: ..."
}
```

**レスポンス:**
```json
{
  "result": "チェック結果の詳細テキスト",
  "conclusion": "OK" or "NG",
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 567
  }
}
```

### `POST /api/check-excel`
Excel一括チェック

**リクエスト:** 
- `multipart/form-data`
- `file`: Excelファイル
- `skill_name`: スキル名（オプション）

**レスポンス:** 
チェック結果を含むExcelファイル

## アーキテクチャ

### データフロー

```
User → Frontend (Browser) → Backend (Flask) → LiteLLM API
  ↑         ↓                    ↓                ↓
Excel     Results            System Prompt    Analysis
File                         (Skills +        Result
                             References)
```

### 技術スタック

| レイヤー | 技術 |
|---------|------|
| Frontend | HTML5, Vanilla JavaScript, CSS3 |
| Backend | Python 3.10+, Flask, pandas, openpyxl |
| LLM | LiteLLM API (gpt-5-mini) |
| Skills | Markdown files (SKILL.md + references/*.md) |
| Data Format | Excel (.xlsx) for input/output |

## 注意事項

- **このツールは一次チェックを支援するものです。最終判断は必ず法務・薬事担当者が行ってください。**
- API呼び出しには料金が発生する場合があります
- 個人情報や機密情報は入力しないでください

## 開発

### 新しいリファレンスの追加

1. `backend/skills/商品コピーチェック/references/` に新しい `.md` ファイルを追加
2. サーバーを再起動

### カスタムスキルの作成

1. `backend/skills/` に新しいディレクトリを作成
2. `SKILL.md` を作成（YAML frontmatter + Markdown）
3. 必要に応じて `references/` ディレクトリを追加

## ライセンス

このプロジェクトは社内ツールです。
