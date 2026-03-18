#!/bin/bash

set -e

echo "=== Keywords Checker - Step Functions Build Script ==="
echo ""

# ビルド出力ディレクトリ
BUILD_DIR="build"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Platform-specific pip settings for Lambda (Python 3.13)
PIP_PLATFORM_FLAGS="--platform manylinux2014_x86_64 --implementation cp --python-version 3.13 --only-binary=:all:"

echo ""
echo "=== Building Lambda Layer (Skills) ==="
echo ""

# Create Lambda Layer for skills files
LAYER_DIR="$BUILD_DIR/layer_python"
mkdir -p "$LAYER_DIR/python/skills"

# Copy skills files to layer
echo "Copying skills files to layer..."
cp -r skills/商品コピーチェック "$LAYER_DIR/python/skills/"

# Create layer ZIP
echo "Creating Lambda Layer ZIP..."
cd "$LAYER_DIR"
zip -r ../skills-layer.zip . -q
cd "$SCRIPT_DIR"

LAYER_SIZE=$(du -h "$BUILD_DIR/skills-layer.zip" | cut -f1)
echo "✅ Lambda Layer created: build/skills-layer.zip ($LAYER_SIZE)"

echo ""
echo "=== Building Splitter Lambda ==="
echo ""

# Create package directory for Splitter
SPLITTER_PACKAGE_DIR="$BUILD_DIR/splitter_package"
mkdir -p "$SPLITTER_PACKAGE_DIR"

# Install dependencies for Splitter
echo "Installing Splitter dependencies..."
if [ -f "splitter/requirements.txt" ]; then
    python3 -m pip install \
        -r splitter/requirements.txt \
        --target "$SPLITTER_PACKAGE_DIR" \
        --upgrade \
        $PIP_PLATFORM_FLAGS
else
    echo "Warning: splitter/requirements.txt not found"
fi

# Copy Splitter Lambda function code
echo "Copying Splitter Lambda function code..."
cp splitter/lambda_function.py "$SPLITTER_PACKAGE_DIR/"

# Create Splitter ZIP
echo "Creating Splitter Lambda ZIP..."
cd "$SPLITTER_PACKAGE_DIR"
zip -r ../splitter.zip . -q
cd "$SCRIPT_DIR"

SPLITTER_SIZE=$(du -h "$BUILD_DIR/splitter.zip" | cut -f1)
echo "✅ Splitter Lambda created: build/splitter.zip ($SPLITTER_SIZE)"

echo ""
echo "=== Building Processor Lambda ==="
echo ""

# Create package directory for Processor
PROCESSOR_PACKAGE_DIR="$BUILD_DIR/processor_package"
mkdir -p "$PROCESSOR_PACKAGE_DIR"

# Install dependencies for Processor
echo "Installing Processor dependencies..."
if [ -f "processor/requirements.txt" ]; then
    python3 -m pip install \
        -r processor/requirements.txt \
        --target "$PROCESSOR_PACKAGE_DIR" \
        --upgrade \
        $PIP_PLATFORM_FLAGS
else
    echo "Warning: processor/requirements.txt not found"
fi

# Copy Processor Lambda function code
echo "Copying Processor Lambda function code..."
cp processor/lambda_function.py "$PROCESSOR_PACKAGE_DIR/"

# Create Processor ZIP
echo "Creating Processor Lambda ZIP..."
cd "$PROCESSOR_PACKAGE_DIR"
zip -r ../processor.zip . -q
cd "$SCRIPT_DIR"

PROCESSOR_SIZE=$(du -h "$BUILD_DIR/processor.zip" | cut -f1)
echo "✅ Processor Lambda created: build/processor.zip ($PROCESSOR_SIZE)"

echo ""
echo "=== Building Combiner Lambda ==="
echo ""

# Create package directory for Combiner
COMBINER_PACKAGE_DIR="$BUILD_DIR/combiner_package"
mkdir -p "$COMBINER_PACKAGE_DIR"

# Install dependencies for Combiner
echo "Installing Combiner dependencies..."
if [ -f "combiner/requirements.txt" ]; then
    python3 -m pip install \
        -r combiner/requirements.txt \
        --target "$COMBINER_PACKAGE_DIR" \
        --upgrade \
        $PIP_PLATFORM_FLAGS
else
    echo "Warning: combiner/requirements.txt not found"
fi

# Copy Combiner Lambda function code
echo "Copying Combiner Lambda function code..."
cp combiner/lambda_function.py "$COMBINER_PACKAGE_DIR/"

# Create Combiner ZIP
echo "Creating Combiner Lambda ZIP..."
cd "$COMBINER_PACKAGE_DIR"
zip -r ../combiner.zip . -q
cd "$SCRIPT_DIR"

COMBINER_SIZE=$(du -h "$BUILD_DIR/combiner.zip" | cut -f1)
echo "✅ Combiner Lambda created: build/combiner.zip ($COMBINER_SIZE)"

echo ""
echo "=== Build Summary ==="
echo ""
echo "Lambda Packages:"
echo "  - build/splitter.zip   ($SPLITTER_SIZE)"
echo "  - build/processor.zip  ($PROCESSOR_SIZE)"
echo "  - build/combiner.zip   ($COMBINER_SIZE)"
echo ""
echo "Lambda Layer:"
echo "  - build/skills-layer.zip ($LAYER_SIZE)"
echo "    Contains: SKILL.md + 200+ reference .md files"
echo ""
echo "Step Functions Definition:"
echo "  - state-machine.json"
echo ""
echo "✅ Build completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Upload Lambda Layer: build/skills-layer.zip"
echo "  2. Upload Lambda packages to AWS Lambda"
echo "  3. Create Step Functions state machine"
echo "  4. Configure EventBridge Rule"
echo ""
echo "See DEPLOY.md for detailed deployment instructions."
