#!/bin/bash

# Deploy Backend to GCP Cloud Run
# Usage: ./deploy.sh [production|staging]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-insuregraph-dev}"
REGION="asia-northeast3"
SERVICE_NAME="insuregraph-backend"
ENVIRONMENT="${1:-production}"

echo -e "${GREEN}🚀 Deploying InsureGraph Backend to Cloud Run${NC}"
echo -e "Project: ${PROJECT_ID}"
echo -e "Region: ${REGION}"
echo -e "Environment: ${ENVIRONMENT}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set GCP project
echo -e "${YELLOW}📍 Setting GCP project...${NC}"
gcloud config set project ${PROJECT_ID}

# Build and deploy
echo -e "${YELLOW}🔨 Building and deploying...${NC}"

if [ "${ENVIRONMENT}" == "production" ]; then
    # Production deployment
    gcloud run deploy ${SERVICE_NAME} \
        --source . \
        --platform managed \
        --region ${REGION} \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --min-instances 0 \
        --max-instances 10 \
        --concurrency 80 \
        --timeout 300 \
        --set-env-vars "ENVIRONMENT=production,DEBUG=false,LOG_LEVEL=INFO" \
        --set-secrets "SECRET_KEY=SECRET_KEY:latest,JWT_SECRET_KEY=JWT_SECRET_KEY:latest,UPSTAGE_API_KEY=UPSTAGE_API_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest" \
        --quiet

else
    # Staging deployment
    gcloud run deploy ${SERVICE_NAME}-staging \
        --source . \
        --platform managed \
        --region ${REGION} \
        --allow-unauthenticated \
        --memory 1Gi \
        --cpu 1 \
        --min-instances 0 \
        --max-instances 3 \
        --set-env-vars "ENVIRONMENT=staging,DEBUG=true,LOG_LEVEL=DEBUG" \
        --quiet
fi

# Get service URL
echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} \
    --format 'value(status.url)')

echo -e "${GREEN}🌐 Service URL:${NC}"
echo "${SERVICE_URL}"
echo ""

# Test health endpoint
echo -e "${YELLOW}🏥 Testing health endpoint...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/api/v1/health")

if [ "${HTTP_CODE}" == "200" ]; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed (HTTP ${HTTP_CODE})${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment successful!${NC}"
echo ""
echo "Next steps:"
echo "1. Update CORS_ORIGINS to include your Vercel domain"
echo "2. Configure Cloud SQL connection"
echo "3. Test API endpoints"
echo ""
echo "View logs:"
echo "  gcloud run logs tail ${SERVICE_NAME} --region ${REGION}"
echo ""
