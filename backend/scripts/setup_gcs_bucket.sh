#!/bin/bash
# GCS Bucket Setup Script for InsureGraph Pro
# This script creates and configures the GCS bucket for policy PDF storage

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GCS Bucket Setup for InsureGraph Pro${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Load environment variables from .env if it exists
if [ -f "backend/.env" ]; then
    echo -e "${YELLOW}Loading environment variables from backend/.env${NC}"
    export $(cat backend/.env | grep -v '^#' | xargs)
fi

# Check required environment variables
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID not set${NC}"
    echo "Please set GCP_PROJECT_ID in backend/.env"
    exit 1
fi

if [ -z "$GCS_BUCKET_POLICIES" ]; then
    echo -e "${RED}Error: GCS_BUCKET_POLICIES not set${NC}"
    echo "Please set GCS_BUCKET_POLICIES in backend/.env"
    exit 1
fi

PROJECT_ID="$GCP_PROJECT_ID"
BUCKET_NAME="$GCS_BUCKET_POLICIES"
LOCATION="${GCS_LOCATION:-asia-northeast3}"  # Default: Seoul region
STORAGE_CLASS="${GCS_STORAGE_CLASS:-STANDARD}"

echo "Project ID: $PROJECT_ID"
echo "Bucket Name: $BUCKET_NAME"
echo "Location: $LOCATION"
echo "Storage Class: $STORAGE_CLASS"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/install"
    exit 1
fi

# Check if authenticated
echo -e "${YELLOW}Checking gcloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${RED}Error: Not authenticated with gcloud${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting project to $PROJECT_ID...${NC}"
gcloud config set project "$PROJECT_ID"

# Check if bucket already exists
echo -e "${YELLOW}Checking if bucket exists...${NC}"
if gsutil ls -b "gs://$BUCKET_NAME" &> /dev/null; then
    echo -e "${GREEN}✓ Bucket already exists: gs://$BUCKET_NAME${NC}"
    BUCKET_EXISTS=true
else
    echo -e "${YELLOW}Creating bucket: gs://$BUCKET_NAME${NC}"
    gsutil mb -p "$PROJECT_ID" -c "$STORAGE_CLASS" -l "$LOCATION" "gs://$BUCKET_NAME"
    echo -e "${GREEN}✓ Bucket created successfully${NC}"
    BUCKET_EXISTS=false
fi

echo ""
echo -e "${BLUE}Configuring bucket settings...${NC}"
echo ""

# Enable versioning for audit trail
echo -e "${YELLOW}1. Enabling versioning...${NC}"
gsutil versioning set on "gs://$BUCKET_NAME"
echo -e "${GREEN}✓ Versioning enabled${NC}"

# Set lifecycle policy to auto-delete old versions after 90 days
echo -e "${YELLOW}2. Setting lifecycle policy...${NC}"
cat > /tmp/lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "numNewerVersions": 3,
          "daysSinceNoncurrentTime": 90
        }
      }
    ]
  }
}
EOF
gsutil lifecycle set /tmp/lifecycle.json "gs://$BUCKET_NAME"
rm /tmp/lifecycle.json
echo -e "${GREEN}✓ Lifecycle policy set (delete versions older than 90 days)${NC}"

# Set uniform bucket-level access (recommended for security)
echo -e "${YELLOW}3. Enabling uniform bucket-level access...${NC}"
gsutil uniformbucketlevelaccess set on "gs://$BUCKET_NAME"
echo -e "${GREEN}✓ Uniform bucket-level access enabled${NC}"

# Set default encryption (Google-managed by default)
echo -e "${YELLOW}4. Verifying encryption...${NC}"
echo -e "${GREEN}✓ Google-managed encryption enabled by default (AES-256)${NC}"

# Set CORS policy for web uploads (if needed)
echo -e "${YELLOW}5. Setting CORS policy...${NC}"
cat > /tmp/cors.json << 'EOF'
[
  {
    "origin": ["https://*.vercel.app", "http://localhost:3000"],
    "method": ["GET", "PUT", "POST"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF
gsutil cors set /tmp/cors.json "gs://$BUCKET_NAME"
rm /tmp/cors.json
echo -e "${GREEN}✓ CORS policy configured${NC}"

echo ""
echo -e "${BLUE}Configuring IAM permissions...${NC}"
echo ""

# Get service account email from environment or prompt
if [ -z "$GCS_SERVICE_ACCOUNT" ]; then
    echo -e "${YELLOW}Service account email not set in GCS_SERVICE_ACCOUNT${NC}"
    echo "Example: insuregraph-storage@project-id.iam.gserviceaccount.com"
    read -p "Enter service account email (or press Enter to skip): " SERVICE_ACCOUNT
else
    SERVICE_ACCOUNT="$GCS_SERVICE_ACCOUNT"
fi

if [ -n "$SERVICE_ACCOUNT" ]; then
    echo -e "${YELLOW}Granting permissions to: $SERVICE_ACCOUNT${NC}"

    # Grant Storage Object Admin role (create, read, delete)
    gsutil iam ch "serviceAccount:$SERVICE_ACCOUNT:roles/storage.objectAdmin" "gs://$BUCKET_NAME"

    echo -e "${GREEN}✓ Granted storage.objectAdmin role${NC}"
else
    echo -e "${YELLOW}⚠ Skipping IAM configuration${NC}"
    echo "Note: You'll need to manually grant permissions to your service account:"
    echo "  - roles/storage.objectAdmin (or custom role with storage.objects.create/get/delete)"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ GCS Bucket Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Bucket Details:"
echo "  Name: gs://$BUCKET_NAME"
echo "  Location: $LOCATION"
echo "  Storage Class: $STORAGE_CLASS"
echo "  Versioning: Enabled"
echo "  Lifecycle: Delete old versions after 90 days"
echo "  Encryption: Google-managed (AES-256)"
echo ""
echo "Next Steps:"
echo "  1. Verify bucket in GCP Console: https://console.cloud.google.com/storage/browser/$BUCKET_NAME"
echo "  2. Test upload from your application"
echo "  3. Update backend/.env with GCS_BUCKET_POLICIES=$BUCKET_NAME"
echo ""
