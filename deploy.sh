#!/bin/bash

# Keywords Checker - Quick Deploy Script for AWS ECS

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Keywords Checker - AWS ECS Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if required tools are installed
check_requirements() {
    echo -e "\n${YELLOW}Checking requirements...${NC}"
    
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}AWS CLI is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All requirements satisfied${NC}"
}

# Load environment variables
load_env() {
    if [ -f ".env.deploy" ]; then
        source .env.deploy
        echo -e "${GREEN}✓ Loaded environment from .env.deploy${NC}"
    else
        echo -e "${RED}Error: .env.deploy file not found${NC}"
        echo -e "${YELLOW}Please create .env.deploy with the following variables:${NC}"
        echo "AWS_ACCOUNT_ID=your-account-id"
        echo "AWS_REGION=ap-northeast-1"
        echo "IMAGE_REPO_NAME=keywords-checker"
        exit 1
    fi
}

# Build Docker image
build_image() {
    echo -e "\n${YELLOW}Building Docker image...${NC}"
    docker build -t ${IMAGE_REPO_NAME}:latest .
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
}

# Push to ECR
push_to_ecr() {
    echo -e "\n${YELLOW}Pushing image to ECR...${NC}"
    
    # ECR login
    aws ecr get-login-password --region ${AWS_REGION} | \
        docker login --username AWS --password-stdin \
        ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
    
    # Tag image
    docker tag ${IMAGE_REPO_NAME}:latest \
        ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_REPO_NAME}:latest
    
    # Push image
    docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_REPO_NAME}:latest
    
    echo -e "${GREEN}✓ Image pushed to ECR successfully${NC}"
}

# Update ECS service
update_service() {
    echo -e "\n${YELLOW}Updating ECS service...${NC}"
    
    aws ecs update-service \
        --cluster keywords-checker-cluster \
        --service keywords-checker-service \
        --force-new-deployment \
        --region ${AWS_REGION}
    
    echo -e "${GREEN}✓ ECS service updated${NC}"
    echo -e "${YELLOW}Waiting for deployment to complete...${NC}"
    
    aws ecs wait services-stable \
        --cluster keywords-checker-cluster \
        --services keywords-checker-service \
        --region ${AWS_REGION}
    
    echo -e "${GREEN}✓ Deployment completed successfully${NC}"
}

# Main execution
main() {
    check_requirements
    load_env
    build_image
    push_to_ecr
    update_service
    
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Run main function
main
