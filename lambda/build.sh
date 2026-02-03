#!/bin/bash

# AWS Lambda デプロイ用ビルドスクリプト
# このスクリプトはLambda1とLambda2のzipファイルを作成します

set -e

echo "==================================="
echo "Lambda Build Script"
echo "==================================="

# プロジェクトルート
PROJECT_ROOT="/Users/abi01711/workspace/keywords-checker"
LAMBDA_DIR="$PROJECT_ROOT/lambda"
BUILD_DIR="$LAMBDA_DIR/build"

# ビルドディレクトリをクリーンアップ
echo "Cleaning build directory..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Lambda Layerのビルド（SKILLファイルとreferenceファイル）
echo ""
echo "==================================="
echo "Building Lambda Layer (skills)..."
echo "==================================="

LAYER_DIR="$LAMBDA_DIR/layer"
rm -rf "$LAYER_DIR"
mkdir -p "$LAYER_DIR/python/skills"

# SKILLファイルとreferenceファイルをコピー
cp -r "$PROJECT_ROOT/backend/skills/商品コピーチェック" "$LAYER_DIR/python/skills/"

# Layer zipファイルを作成
cd "$LAYER_DIR"
zip -r "$BUILD_DIR/skills-layer.zip" python/ -x "*.pyc" -x "*__pycache__*"
echo "✅ Layer zip created: $BUILD_DIR/skills-layer.zip"

# Lambda1のビルド
echo ""
echo "==================================="
echo "Building Lambda1..."
echo "==================================="

LAMBDA1_DIR="$LAMBDA_DIR/lambda1"
LAMBDA1_PACKAGE="$LAMBDA1_DIR/package"

# パッケージディレクトリをクリーンアップ
rm -rf "$LAMBDA1_PACKAGE"
mkdir -p "$LAMBDA1_PACKAGE"

# 依存関係をインストール
echo "Installing Lambda1 dependencies..."
pip install -r "$LAMBDA1_DIR/requirements.txt" -t "$LAMBDA1_PACKAGE" --quiet

# lambda_function.pyをコピー
cp "$LAMBDA1_DIR/lambda_function.py" "$LAMBDA1_PACKAGE/"

# zipファイルを作成
cd "$LAMBDA1_PACKAGE"
zip -r "$BUILD_DIR/lambda1.zip" . -x "*.pyc" -x "*__pycache__*"
echo "✅ Lambda1 zip created: $BUILD_DIR/lambda1.zip"

# Lambda2のビルド
echo ""
echo "==================================="
echo "Building Lambda2..."
echo "==================================="

LAMBDA2_DIR="$LAMBDA_DIR/lambda2"
LAMBDA2_PACKAGE="$LAMBDA2_DIR/package"

# パッケージディレクトリをクリーンアップ
rm -rf "$LAMBDA2_PACKAGE"
mkdir -p "$LAMBDA2_PACKAGE"

# 依存関係をインストール
echo "Installing Lambda2 dependencies..."
pip install -r "$LAMBDA2_DIR/requirements.txt" -t "$LAMBDA2_PACKAGE" --quiet

# lambda_function.pyをコピー
cp "$LAMBDA2_DIR/lambda_function.py" "$LAMBDA2_PACKAGE/"

# zipファイルを作成
cd "$LAMBDA2_PACKAGE"
zip -r "$BUILD_DIR/lambda2.zip" . -x "*.pyc" -x "*__pycache__*"
echo "✅ Lambda2 zip created: $BUILD_DIR/lambda2.zip"

# ビルド完了
echo ""
echo "==================================="
echo "Build Complete!"
echo "==================================="
echo ""
echo "Created files:"
echo "  - $BUILD_DIR/skills-layer.zip"
echo "  - $BUILD_DIR/lambda1.zip"
echo "  - $BUILD_DIR/lambda2.zip"
echo ""
echo "File sizes:"
ls -lh "$BUILD_DIR"/*.zip
echo ""
echo "Next steps:"
echo "1. Upload skills-layer.zip as Lambda Layer"
echo "2. Upload lambda1.zip to Lambda1 function"
echo "3. Upload lambda2.zip to Lambda2 function"
echo ""
echo "See lambda/DEPLOY.md for detailed deployment instructions."
