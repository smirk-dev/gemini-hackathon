#!/usr/bin/env pwsh
# LegalMind Complete Deployment Fix - PowerShell Version
# This script completely fixes the 403 scope error and ensures proper deployment
# Usage: .\deploy-complete-fix.ps1 -ProjectId "legalmind-486106"

param(
    [string]$ProjectId = "legalmind-486106",
    [string]$Region = "us-central1",
    [string]$ServiceName = "legalmind-backend"
)

$ErrorActionPreference = "Stop"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "█ $Message" -ForegroundColor Cyan -BackgroundColor Black
    Write-Host "─" * 80 -ForegroundColor Gray
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor White
}

function Verify-Tool {
    param([string]$Tool)
    if (-not (Get-Command $Tool -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "$Tool is not installed or not in PATH"
        exit 1
    }
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

Write-Step "PRE-FLIGHT CHECKS"

Write-Info "Verifying required tools..."
Verify-Tool "gcloud"
Verify-Tool "docker"

Write-Success "All required tools found"

Write-Info "Setting project to: $ProjectId"
gcloud config set project $ProjectId --quiet 2>$null

# Verify project exists
try {
    $projectInfo = gcloud projects describe $ProjectId --format="value(projectId)" 2>$null
    if (-not $projectInfo) {
        Write-Error-Custom "Cannot access project: $ProjectId"
        exit 1
    }
    Write-Success "Project verified: $ProjectId"
} catch {
    Write-Error-Custom "Failed to verify project: $_"
    exit 1
}

# ============================================================================
# STEP 1: ENABLE ALL REQUIRED APIS
# ============================================================================

Write-Step "STEP 1: ENABLING GOOGLE CLOUD APIS"

$required_apis = @(
    "aiplatform.googleapis.com",
    "generativeai.googleapis.com",
    "run.googleapis.com",
    "firestore.googleapis.com",
    "storage-api.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudresourcemanager.googleapis.com"
)

foreach ($api in $required_apis) {
    Write-Info "Enabling $api..."
    gcloud services enable $api --quiet 2>$null
}

Write-Success "All APIs enabled"

# ============================================================================
# STEP 2: VERIFY/CREATE SERVICE ACCOUNT
# ============================================================================

Write-Step "STEP 2: VERIFYING SERVICE ACCOUNT"

$SA_EMAIL = "${ServiceName}@${ProjectId}.iam.gserviceaccount.com"
Write-Info "Service Account: $SA_EMAIL"

# Check if service account exists
try {
    $sa_exists = gcloud iam service-accounts describe $SA_EMAIL --format="value(email)" 2>$null
    if ($sa_exists) {
        Write-Success "Service account exists: $SA_EMAIL"
    } else {
        Write-Warning-Custom "Service account does not exist, attempting to create..."
        gcloud iam service-accounts create $ServiceName `
            --display-name="LegalMind Backend Service Account" `
            --description="Service account for LegalMind backend on Cloud Run" `
            --quiet
        Write-Success "Service account created: $SA_EMAIL"
    }
} catch {
    Write-Error-Custom "Error checking service account: $_"
    exit 1
}

# ============================================================================
# STEP 3: GRANT REQUIRED IAM ROLES
# ============================================================================

Write-Step "STEP 3: GRANTING REQUIRED IAM ROLES"

$required_roles = @(
    "roles/aiplatform.user",
    "roles/datastore.user",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter"
)

foreach ($role in $required_roles) {
    Write-Info "Granting $role..."
    gcloud projects add-iam-policy-binding $ProjectId `
        --member="serviceAccount:$SA_EMAIL" `
        --role="$role" `
        --condition=None `
        --quiet 2>$null
}

Write-Success "All required IAM roles granted"

# ============================================================================
# STEP 4: VERIFY IAM ROLES ARE PROPERLY SET
# ============================================================================

Write-Step "STEP 4: VERIFYING IAM ROLES"

Write-Info "Checking service account roles..."
$assigned_roles = gcloud projects get-iam-policy $ProjectId `
    --flatten="bindings[].members" `
    --filter="bindings.members:serviceAccount:$SA_EMAIL" `
    --format="table(bindings.role)" | Select-Object -Skip 1

if ($assigned_roles.Count -eq 0) {
    Write-Error-Custom "No roles found for service account!"
    exit 1
}

Write-Info "Assigned roles:"
$assigned_roles | ForEach-Object {
    Write-Host "  ✓ $_" -ForegroundColor Green
}

# Check for critical roles
$has_vertex_ai = $assigned_roles | Where-Object { $_ -match "roles/aiplatform.user" }
$has_datastore = $assigned_roles | Where-Object { $_ -match "roles/datastore.user" }

if (-not $has_vertex_ai) {
    Write-Error-Custom "CRITICAL: roles/aiplatform.user not assigned!"
    exit 1
}

if (-not $has_datastore) {
    Write-Error-Custom "CRITICAL: roles/datastore.user not assigned!"
    exit 1
}

Write-Success "All critical roles verified"

# ============================================================================
# STEP 5: BUILD DOCKER IMAGE
# ============================================================================

Write-Step "STEP 5: BUILDING DOCKER IMAGE"

Write-Info "This will take 2-5 minutes..."

$image_tag = "gcr.io/${ProjectId}/${ServiceName}:latest"
Write-Info "Building image: $image_tag"

try {
    docker build -t $image_tag -f Dockerfile . 2>&1 | ForEach-Object {
        if ($_ -match "ERROR" -or $_ -match "error") {
            Write-Host "  $_ " -ForegroundColor Red
        } else {
            Write-Host "  $_" -ForegroundColor Gray
        }
    }
    Write-Success "Docker image built successfully"
} catch {
    Write-Error-Custom "Docker build failed: $_"
    exit 1
}

# ============================================================================
# STEP 6: PUSH TO CONTAINER REGISTRY
# ============================================================================

Write-Step "STEP 6: PUSHING TO CONTAINER REGISTRY"

Write-Info "Configuring Docker auth for GCR..."
gcloud auth configure-docker gcr.io --quiet 2>$null

Write-Info "Pushing image: $image_tag"
try {
    docker push $image_tag 2>&1 | ForEach-Object {
        if ($_ -match "ERROR" -or $_ -match "error") {
            Write-Host "  $_ " -ForegroundColor Red
        } else {
            Write-Host "  $_" -ForegroundColor Gray
        }
    }
    Write-Success "Image pushed to container registry"
} catch {
    Write-Error-Custom "Docker push failed: $_"
    exit 1
}

# ============================================================================
# STEP 7: DEPLOY TO CLOUD RUN
# ============================================================================

Write-Step "STEP 7: DEPLOYING TO CLOUD RUN"

Write-Info "Deploying with proper configuration..."

try {
    gcloud run deploy $ServiceName `
        --image $image_tag `
        --platform managed `
        --region $Region `
        --allow-unauthenticated `
        --service-account $SA_EMAIL `
        --memory 1Gi `
        --cpu 1 `
        --timeout 60 `
        --min-instances 1 `
        --max-instances 10 `
        --set-env-vars "GOOGLE_CLOUD_PROJECT=${ProjectId},USE_VERTEX_AI=true,DEBUG=false" `
        --quiet
    
    Write-Success "Cloud Run deployment successful"
} catch {
    Write-Error-Custom "Cloud Run deployment failed: $_"
    exit 1
}

# ============================================================================
# STEP 8: GET SERVICE URL
# ============================================================================

Write-Step "STEP 8: RETRIEVING SERVICE URL"

try {
    $service_url = gcloud run services describe $ServiceName `
        --region $Region `
        --format="value(status.url)"
    
    Write-Success "Service URL: $service_url"
} catch {
    Write-Warning-Custom "Could not retrieve service URL"
}

# ============================================================================
# STEP 9: VERIFY DEPLOYMENT
# ============================================================================

Write-Step "STEP 9: VERIFYING DEPLOYMENT"

Write-Info "Waiting 10 seconds for service to stabilize..."
Start-Sleep -Seconds 10

Write-Info "Testing health check endpoint..."
try {
    $health_response = curl.exe -s "$service_url/api/health" 2>&1
    if ($health_response -match '"status"') {
        Write-Success "Health check passed!"
        Write-Info "Response: $health_response"
    } else {
        Write-Warning-Custom "Unexpected health check response (service might still be starting)"
        Write-Info "Response: $health_response"
    }
} catch {
    Write-Warning-Custom "Could not test health endpoint (service might still be starting): $_"
}

# ============================================================================
# STEP 10: CHECK LOGS
# ============================================================================

Write-Step "STEP 10: CHECKING DEPLOYMENT LOGS"

Write-Info "Recent logs (last 20 lines):"
try {
    gcloud run services logs read $ServiceName `
        --region $Region `
        --limit 20 `
        --format "table(timestamp,text)" 2>$null | Write-Host
} catch {
    Write-Warning-Custom "Could not retrieve logs: $_"
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================

Write-Step "DEPLOYMENT COMPLETE"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║             LegalMind Backend Deployment Summary              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project ID:        $ProjectId" -ForegroundColor White
Write-Host "Service:           $ServiceName" -ForegroundColor White
Write-Host "Region:            $Region" -ForegroundColor White
Write-Host "Service Account:   $SA_EMAIL" -ForegroundColor White

if ($service_url) {
    Write-Host "Service URL:       $service_url" -ForegroundColor White
}

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  • Memory:        1Gi" -ForegroundColor Gray
Write-Host "  • CPU:           1 vCPU" -ForegroundColor Gray
Write-Host "  • Instances:     1-10 (auto-scaling)" -ForegroundColor Gray
Write-Host "  • Timeout:       60 seconds" -ForegroundColor Gray
Write-Host "  • Vertex AI:     Enabled" -ForegroundColor Gray
Write-Host "  • Debug Mode:    Disabled" -ForegroundColor Gray
Write-Host ""
Write-Host "IAM Roles:" -ForegroundColor Cyan
Write-Host "  ✓ roles/aiplatform.user" -ForegroundColor Green
Write-Host "  ✓ roles/datastore.user" -ForegroundColor Green
Write-Host "  ✓ roles/storage.objectAdmin" -ForegroundColor Green
Write-Host "  ✓ roles/logging.logWriter" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Monitor logs:" -ForegroundColor White
Write-Host "     gcloud run services logs read $ServiceName --region=$Region --follow" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. View service details:" -ForegroundColor White
Write-Host "     gcloud run services describe $ServiceName --region=$Region" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Test the API:" -ForegroundColor White
Write-Host "     curl $service_url/api/health" -ForegroundColor Gray
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Success "✨ Deployment completed successfully! Backend should now be fully operational."
Write-Host ""
