#!/bin/bash

# LegalMind GCP Deployment Setup Script
# This script automates the setup of Google Cloud resources

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it from https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install it from https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_error "Node.js/npm is not installed. Please install it from https://nodejs.org/"
    exit 1
fi

print_info "Prerequisites check passed!"

# Get project ID
read -p "Enter your Google Cloud Project ID: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    print_error "Project ID cannot be empty"
    exit 1
fi

print_info "Using project: $PROJECT_ID"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
print_info "Enabling Google Cloud APIs..."
gcloud services enable \
    run.googleapis.com \
    firestore.googleapis.com \
    storage-api.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    firebase.googleapis.com \
    artifactregistry.googleapis.com \
    iam.googleapis.com \
    iamcredentials.googleapis.com \
    cloudresourcemanager.googleapis.com \
    aiplatform.googleapis.com \
    generativeai.googleapis.com

print_info "APIs enabled successfully!"

# Create service account for Cloud Run
print_info "Creating service account for Cloud Run..."

SERVICE_ACCOUNT_EMAIL="legalmind-backend@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account exists
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &> /dev/null; then
    print_warning "Service account already exists: $SERVICE_ACCOUNT_EMAIL"
else
    gcloud iam service-accounts create legalmind-backend \
        --display-name="LegalMind Backend Service Account" \
        --description="Service account for LegalMind backend on Cloud Run"
    print_info "Service account created: $SERVICE_ACCOUNT_EMAIL"
fi

# Grant roles to service account
print_info "Granting roles to service account..."

roles=(
    "roles/datastore.user"
    "roles/storage.objectAdmin"
    "roles/secretmanager.secretAccessor"
    "roles/logging.logWriter"
    "roles/aiplatform.user"
)

for role in "${roles[@]}"; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role" \
        --quiet
    print_info "Granted role: $role"
done

# Create GitHub Actions service account
print_info "Setting up GitHub Actions integration..."

GITHUB_SA_EMAIL="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe $GITHUB_SA_EMAIL &> /dev/null; then
    print_warning "GitHub Actions service account already exists: $GITHUB_SA_EMAIL"
else
    gcloud iam service-accounts create github-actions \
        --display-name="GitHub Actions Service Account" \
        --description="Service account for GitHub Actions CI/CD"
    print_info "GitHub Actions service account created: $GITHUB_SA_EMAIL"
fi

# Grant necessary roles to GitHub Actions SA
print_info "Granting roles to GitHub Actions service account..."

github_roles=(
    "roles/run.admin"
    "roles/storage.admin"
    "roles/container.developer"
)

for role in "${github_roles[@]}"; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$GITHUB_SA_EMAIL" \
        --role="$role" \
        --quiet
    print_info "Granted role: $role"
done

# Setup Workload Identity Federation
print_info "Setting up Workload Identity Federation for GitHub..."

POOL_ID="github-pool"
PROVIDER_ID="github-provider"

# Check if pool exists
if gcloud iam workload-identity-pools describe $POOL_ID --location=global &> /dev/null; then
    print_warning "Workload Identity Pool already exists: $POOL_ID"
else
    gcloud iam workload-identity-pools create $POOL_ID \
        --project=$PROJECT_ID \
        --location=global \
        --display-name="GitHub Actions Pool"
    print_info "Created Workload Identity Pool: $POOL_ID"
fi

# Get the pool resource name
WORKLOAD_IDENTITY_POOL_ID=$(gcloud iam workload-identity-pools describe $POOL_ID \
    --location=global \
    --format='value(name)')

# Check if provider exists
if gcloud iam workload-identity-pools providers describe $PROVIDER_ID \
    --location=global \
    --workload-identity-pool=$POOL_ID &> /dev/null; then
    print_warning "Workload Identity Provider already exists: $PROVIDER_ID"
else
    gcloud iam workload-identity-pools providers create-oidc $PROVIDER_ID \
        --project=$PROJECT_ID \
        --location=global \
        --workload-identity-pool=$POOL_ID \
        --display-name="GitHub Provider" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.environment=assertion.environment,attribute.repository=assertion.repository" \
        --issuer-uri="https://token.actions.githubusercontent.com"
    print_info "Created Workload Identity Provider: $PROVIDER_ID"
fi

# Configure service account impersonation
print_info "Configuring Workload Identity impersonation..."

gcloud iam service-accounts add-iam-policy-binding $GITHUB_SA_EMAIL \
    --role=roles/iam.workloadIdentityUser \
    --member="principalSet://iam.googleapis.com/projects/$PROJECT_ID/locations/global/workloadIdentityPools/$POOL_ID/attribute.repository/smirk-dev/gemini-hackathon" \
    --quiet

print_info "Workload Identity configured!"

# Create Cloud Storage buckets if they don't exist
print_info "Setting up Cloud Storage buckets..."

DOCUMENTS_BUCKET="${PROJECT_ID}-documents"
ARTIFACTS_BUCKET="${PROJECT_ID}-artifacts"

for bucket in $DOCUMENTS_BUCKET $ARTIFACTS_BUCKET; do
    if gsutil ls -b gs://$bucket &> /dev/null; then
        print_warning "Bucket already exists: gs://$bucket"
    else
        gsutil mb -p $PROJECT_ID gs://$bucket
        print_info "Created bucket: gs://$bucket"
    fi
done

# Create secrets in Secret Manager
print_info "Setting up secrets in Secret Manager..."

read -p "Enter your Google API Key (or press Enter to skip): " GOOGLE_API_KEY
if [ ! -z "$GOOGLE_API_KEY" ]; then
    echo -n "$GOOGLE_API_KEY" | gcloud secrets create GOOGLE_API_KEY --data-file=- --replication-policy="automatic" 2>/dev/null || {
        gcloud secrets versions add GOOGLE_API_KEY --data-file=-  <<< "$GOOGLE_API_KEY"
    }
    print_info "Created secret: GOOGLE_API_KEY"
fi

read -p "Enter your Gemini API Key (or press Enter to skip): " GEMINI_API_KEY
if [ ! -z "$GEMINI_API_KEY" ]; then
    echo -n "$GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=- --replication-policy="automatic" 2>/dev/null || {
        gcloud secrets versions add GEMINI_API_KEY --data-file=- <<< "$GEMINI_API_KEY"
    }
    print_info "Created secret: GEMINI_API_KEY"
fi

# Grant Cloud Run service account access to secrets
print_info "Granting secret access to Cloud Run service account..."

for secret in GOOGLE_API_KEY GEMINI_API_KEY; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet 2>/dev/null || true
done

# Display summary
print_info "==============================================="
print_info "GCP Setup Complete!"
print_info "==============================================="
print_info ""
print_info "Project ID: $PROJECT_ID"
print_info "Cloud Run Service Account: $SERVICE_ACCOUNT_EMAIL"
print_info "GitHub Actions Service Account: $GITHUB_SA_EMAIL"
print_info "Workload Identity Pool: $WORKLOAD_IDENTITY_POOL_ID"
print_info ""
print_warning "Next Steps:"
echo ""
echo "1. Save these values as GitHub Secrets:"
echo "   - GCP_PROJECT_ID: $PROJECT_ID"
echo "   - WIF_PROVIDER: $WORKLOAD_IDENTITY_POOL_ID"
echo "   - WIF_SERVICE_ACCOUNT: $GITHUB_SA_EMAIL"
echo ""
echo "2. Create Firebase Service Account key:"
echo "   gcloud iam service-accounts keys create firebase-key.json \\"
echo "     --iam-account=$SERVICE_ACCOUNT_EMAIL"
echo "   # Then base64 encode and add as FIREBASE_SERVICE_ACCOUNT secret"
echo ""
echo "3. Deploy backend:"
echo "   git push origin main"
echo ""
echo "4. View deployment status:"
echo "   gcloud run services list --region us-central1"
echo ""
print_info "==============================================="
