# LegalMind GCP Deployment Setup Script (Windows PowerShell)
# This script automates the setup of Google Cloud resources

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check prerequisites
Write-Info "Checking prerequisites..."

$prerequisites = @("gcloud", "docker", "npm")
foreach ($tool in $prerequisites) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Error "$tool is not installed. Please install it first."
        exit 1
    }
}

Write-Info "Prerequisites check passed!"

# Get project ID
$PROJECT_ID = Read-Host "Enter your Google Cloud Project ID"

if ([string]::IsNullOrEmpty($PROJECT_ID)) {
    Write-Error "Project ID cannot be empty"
    exit 1
}

Write-Info "Using project: $PROJECT_ID"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
Write-Info "Enabling Google Cloud APIs..."
$apis = @(
    "run.googleapis.com",
    "firestore.googleapis.com",
    "storage-api.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "firebase.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudresourcemanager.googleapis.com"
)

foreach ($api in $apis) {
    gcloud services enable $api --quiet
}

Write-Info "APIs enabled successfully!"

# Create service account for Cloud Run
Write-Info "Creating service account for Cloud Run..."

$SERVICE_ACCOUNT_EMAIL = "legalmind-backend@${PROJECT_ID}.iam.gserviceaccount.com"

try {
    gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL 2>$null
    Write-Warning "Service account already exists: $SERVICE_ACCOUNT_EMAIL"
} catch {
    gcloud iam service-accounts create legalmind-backend `
        --display-name="LegalMind Backend Service Account" `
        --description="Service account for LegalMind backend on Cloud Run"
    Write-Info "Service account created: $SERVICE_ACCOUNT_EMAIL"
}

# Grant roles to service account
Write-Info "Granting roles to service account..."

$roles = @(
    "roles/datastore.user",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter"
)

foreach ($role in $roles) {
    gcloud projects add-iam-policy-binding $PROJECT_ID `
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
        --role="$role" `
        --quiet
    Write-Info "Granted role: $role"
}

# Create GitHub Actions service account
Write-Info "Setting up GitHub Actions integration..."

$GITHUB_SA_EMAIL = "github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

try {
    gcloud iam service-accounts describe $GITHUB_SA_EMAIL 2>$null
    Write-Warning "GitHub Actions service account already exists: $GITHUB_SA_EMAIL"
} catch {
    gcloud iam service-accounts create github-actions `
        --display-name="GitHub Actions Service Account" `
        --description="Service account for GitHub Actions CI/CD"
    Write-Info "GitHub Actions service account created: $GITHUB_SA_EMAIL"
}

# Grant necessary roles to GitHub Actions SA
Write-Info "Granting roles to GitHub Actions service account..."

$github_roles = @(
    "roles/run.admin",
    "roles/storage.admin",
    "roles/container.developer"
)

foreach ($role in $github_roles) {
    gcloud projects add-iam-policy-binding $PROJECT_ID `
        --member="serviceAccount:$GITHUB_SA_EMAIL" `
        --role="$role" `
        --quiet
    Write-Info "Granted role: $role"
}

# Setup Workload Identity Federation
Write-Info "Setting up Workload Identity Federation for GitHub..."

$POOL_ID = "github-pool"
$PROVIDER_ID = "github-provider"

try {
    gcloud iam workload-identity-pools describe $POOL_ID --location=global 2>$null
    Write-Warning "Workload Identity Pool already exists: $POOL_ID"
} catch {
    gcloud iam workload-identity-pools create $POOL_ID `
        --project=$PROJECT_ID `
        --location=global `
        --display-name="GitHub Actions Pool"
    Write-Info "Created Workload Identity Pool: $POOL_ID"
}

# Get the pool resource name
$WORKLOAD_IDENTITY_POOL_ID = gcloud iam workload-identity-pools describe $POOL_ID `
    --location=global `
    --format='value(name)'

# Check if provider exists
try {
    gcloud iam workload-identity-pools providers describe $PROVIDER_ID `
        --location=global `
        --workload-identity-pool=$POOL_ID 2>$null
    Write-Warning "Workload Identity Provider already exists: $PROVIDER_ID"
} catch {
    gcloud iam workload-identity-pools providers create-oidc $PROVIDER_ID `
        --project=$PROJECT_ID `
        --location=global `
        --workload-identity-pool=$POOL_ID `
        --display-name="GitHub Provider" `
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.environment=assertion.environment,attribute.repository=assertion.repository" `
        --issuer-uri="https://token.actions.githubusercontent.com"
    Write-Info "Created Workload Identity Provider: $PROVIDER_ID"
}

# Configure service account impersonation
Write-Info "Configuring Workload Identity impersonation..."

gcloud iam service-accounts add-iam-policy-binding $GITHUB_SA_EMAIL `
    --role=roles/iam.workloadIdentityUser `
    --member="principalSet://iam.googleapis.com/projects/$PROJECT_ID/locations/global/workloadIdentityPools/$POOL_ID/attribute.repository/smirk-dev/gemini-hackathon" `
    --quiet

Write-Info "Workload Identity configured!"

# Create Cloud Storage buckets if they don't exist
Write-Info "Setting up Cloud Storage buckets..."

$DOCUMENTS_BUCKET = "$PROJECT_ID-documents"
$ARTIFACTS_BUCKET = "$PROJECT_ID-artifacts"

foreach ($bucket in $DOCUMENTS_BUCKET, $ARTIFACTS_BUCKET) {
    try {
        gsutil ls -b "gs://$bucket" 2>$null
        Write-Warning "Bucket already exists: gs://$bucket"
    } catch {
        gsutil mb -p $PROJECT_ID "gs://$bucket"
        Write-Info "Created bucket: gs://$bucket"
    }
}

# Display summary
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Info "GCP Setup Complete!"
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "Project ID: $PROJECT_ID"
Write-Info "Cloud Run Service Account: $SERVICE_ACCOUNT_EMAIL"
Write-Info "GitHub Actions Service Account: $GITHUB_SA_EMAIL"
Write-Info "Workload Identity Pool: $WORKLOAD_IDENTITY_POOL_ID"
Write-Host ""
Write-Warning "Next Steps:"
Write-Host ""
Write-Host "1. Save these values as GitHub Secrets:"
Write-Host "   - GCP_PROJECT_ID: $PROJECT_ID"
Write-Host "   - WIF_PROVIDER: $WORKLOAD_IDENTITY_POOL_ID"
Write-Host "   - WIF_SERVICE_ACCOUNT: $GITHUB_SA_EMAIL"
Write-Host ""
Write-Host "2. Create Firebase Service Account key:"
Write-Host "   gcloud iam service-accounts keys create firebase-key.json \" -ForegroundColor Gray
Write-Host "     --iam-account=$SERVICE_ACCOUNT_EMAIL" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Deploy backend:"
Write-Host "   git push origin main"
Write-Host ""
Write-Host "4. View deployment status:"
Write-Host "   gcloud run services list --region us-central1"
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
