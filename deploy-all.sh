#!/bin/bash

# ============================================
# Keywords Checker - 完全デプロイスクリプト
# ECS + Lambda + EventBridge + S3 を一括デプロイ
# ============================================

set -e

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 設定
PROJECT_NAME="keywords-checker"
AWS_REGION="ap-northeast-1"
STACK_NAME="${PROJECT_NAME}-stack"

# 関数: メッセージ出力
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 関数: 必須パラメータチェック
check_requirements() {
    log_info "必須ツールを確認中..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI がインストールされていません"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker がインストールされていません"
        exit 1
    fi
    
    log_success "必須ツールの確認完了"
}

# 関数: AWS認証情報確認
check_aws_credentials() {
    log_info "AWS認証情報を確認中..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS認証情報が設定されていません"
        exit 1
    fi
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    log_success "AWS Account ID: $AWS_ACCOUNT_ID"
}

# 関数: LiteLLM API Key入力
get_litellm_api_key() {
    if [ -z "$LITELLM_API_KEY" ]; then
        echo -e "${YELLOW}LiteLLM API Keyを入力してください:${NC}"
        read -s LITELLM_API_KEY
        
        if [ -z "$LITELLM_API_KEY" ]; then
            log_error "API Keyが入力されていません"
            exit 1
        fi
    fi
    
    log_success "API Key取得完了"
}

# 関数: ECRリポジトリ作成
create_ecr_repository() {
    log_info "ECRリポジトリを作成中..."
    
    REPO_NAME="${PROJECT_NAME}"
    
    if aws ecr describe-repositories --repository-names $REPO_NAME --region $AWS_REGION &> /dev/null; then
        log_warning "ECRリポジトリは既に存在します"
    else
        aws ecr create-repository \
            --repository-name $REPO_NAME \
            --region $AWS_REGION \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256
        log_success "ECRリポジトリ作成完了"
    fi
    
    ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"
    log_info "ECR URI: $ECR_REPO_URI"
}

# 関数: Dockerイメージビルド & プッシュ
build_and_push_docker() {
    log_info "Dockerイメージをビルド中..."
    
    # ECRログイン
    aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin $ECR_REPO_URI
    
    # Dockerイメージビルド
    docker build -t $PROJECT_NAME:latest .
    
    # タグ付け
    docker tag $PROJECT_NAME:latest $ECR_REPO_URI:latest
    docker tag $PROJECT_NAME:latest $ECR_REPO_URI:$(date +%Y%m%d-%H%M%S)
    
    # プッシュ
    log_info "Dockerイメージをプッシュ中..."
    docker push $ECR_REPO_URI:latest
    docker push $ECR_REPO_URI:$(date +%Y%m%d-%H%M%S)
    
    log_success "Dockerイメージプッシュ完了"
    
    DOCKER_IMAGE_URI="${ECR_REPO_URI}:latest"
}

# 関数: CloudFormationスタックデプロイ
deploy_cloudformation() {
    log_info "CloudFormationスタックをデプロイ中..."
    
    # パラメータファイル作成
    cat > /tmp/cf-parameters.json <<EOF
[
  {
    "ParameterKey": "ProjectName",
    "ParameterValue": "${PROJECT_NAME}"
  },
  {
    "ParameterKey": "LiteLLMApiKey",
    "ParameterValue": "${LITELLM_API_KEY}"
  },
  {
    "ParameterKey": "DockerImageUri",
    "ParameterValue": "${DOCKER_IMAGE_URI}"
  }
]
EOF
    
    # スタック存在確認
    if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION &> /dev/null; then
        log_info "既存スタックを更新中..."
        
        aws cloudformation update-stack \
            --stack-name $STACK_NAME \
            --template-body file://cloudformation/keywords-checker-stack.yaml \
            --parameters file:///tmp/cf-parameters.json \
            --capabilities CAPABILITY_NAMED_IAM \
            --region $AWS_REGION || {
                if [ $? -eq 254 ]; then
                    log_warning "変更なし - スタックは既に最新です"
                else
                    log_error "スタック更新失敗"
                    exit 1
                fi
            }
        
        OPERATION="update"
    else
        log_info "新規スタックを作成中..."
        
        aws cloudformation create-stack \
            --stack-name $STACK_NAME \
            --template-body file://cloudformation/keywords-checker-stack.yaml \
            --parameters file:///tmp/cf-parameters.json \
            --capabilities CAPABILITY_NAMED_IAM \
            --region $AWS_REGION
        
        OPERATION="create"
    fi
    
    # スタック完了待機
    if [ "$OPERATION" != "" ]; then
        log_info "CloudFormationスタックの完了を待機中... (5〜10分かかります)"
        
        aws cloudformation wait stack-${OPERATION}-complete \
            --stack-name $STACK_NAME \
            --region $AWS_REGION
        
        log_success "CloudFormationスタックデプロイ完了"
    fi
    
    # クリーンアップ
    rm -f /tmp/cf-parameters.json
}

# 関数: 出力値取得
get_stack_outputs() {
    log_info "デプロイ結果を取得中..."
    
    OUTPUTS=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $AWS_REGION \
        --query 'Stacks[0].Outputs' \
        --output json)
    
    ALB_URL=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="ALBURL") | .OutputValue')
    EXCEL_BUCKET=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="ExcelBucketName") | .OutputValue')
    SKILLS_BUCKET=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="SkillsBucketName") | .OutputValue')
    REDIS_ENDPOINT=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="RedisEndpoint") | .OutputValue')
    
    echo ""
    echo "============================================"
    echo "  デプロイ完了 🎉"
    echo "============================================"
    echo ""
    echo -e "${GREEN}Application URL:${NC}"
    echo "  $ALB_URL"
    echo ""
    echo -e "${GREEN}S3 Buckets:${NC}"
    echo "  Excel: $EXCEL_BUCKET"
    echo "  Skills: $SKILLS_BUCKET"
    echo ""
    echo -e "${GREEN}Redis Cache:${NC}"
    echo "  Endpoint: $REDIS_ENDPOINT:6379"
    echo ""
    echo -e "${GREEN}次のステップ:${NC}"
    echo "  1. Health Check:"
    echo "     curl $ALB_URL/api/health"
    echo ""
    echo "  2. Skillsファイルアップロード:"
    echo "     aws s3 cp .github/skills/商品コピーチェック/SKILL.md s3://$SKILLS_BUCKET/"
    echo "     aws s3 cp .github/skills/商品コピーチェック/references/ s3://$SKILLS_BUCKET/references/ --recursive"
    echo ""
    echo "  3. Excelファイルアップロード:"
    echo "     aws s3 cp test.xlsx s3://$EXCEL_BUCKET/input/"
    echo ""
    echo "  4. 処理結果確認:"
    echo "     aws s3 ls s3://$EXCEL_BUCKET/output/"
    echo ""
    echo "  5. ログ確認:"
    echo "     aws logs tail /ecs/$PROJECT_NAME --follow"
    echo ""
    echo "============================================"
}

# 関数: ロールバック
rollback() {
    log_error "デプロイ中にエラーが発生しました"
    log_warning "ロールバックしますか？ (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "スタックを削除中..."
        aws cloudformation delete-stack \
            --stack-name $STACK_NAME \
            --region $AWS_REGION
        log_success "削除完了"
    fi
}

# メイン処理
main() {
    echo "============================================"
    echo "  Keywords Checker - 完全デプロイ"
    echo "============================================"
    echo ""
    
    # エラーハンドリング
    trap rollback ERR
    
    # 実行
    check_requirements
    check_aws_credentials
    get_litellm_api_key
    create_ecr_repository
    build_and_push_docker
    deploy_cloudformation
    get_stack_outputs
}

# スクリプト実行
main "$@"
