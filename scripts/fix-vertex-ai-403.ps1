#!/usr/bin/env pwsh

# Fix Vertex AI 403 Authentication Scope Error
# Grants proper IAM permissions to Cloud Run service account

$projectId = "legalmind-486106"
$region = "us-central1"
$backendService = "legalmind-backend"
$projectNumber = "677928716377"

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Fixing Vertex AI Authentication Scope Error              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Set project
Write-Host "✓ Setting project..." -ForegroundColor Green
gcloud config set project $projectId --quiet

# Get the Cloud Run service account
Write-Host "✓ Getting Cloud Run service account..." -ForegroundColor Green
$serviceAccount = "$projectNumber-compute@developer.gserviceaccount.com"
Write-Host "  Service Account: $serviceAccount" -ForegroundColor White

# Grant required IAM roles
Write-Host ""
Write-Host "✓ Granting IAM permissions..." -ForegroundColor Green

$roles = @(
    "roles/aiplatform.user",
    "roles/ml.developer",
    "roles/datastore.user",
    "roles/storage.objectAdmin"
)

foreach ($role in $roles) {
    Write-Host "  Adding $role..." -ForegroundColor White
    gcloud projects add-iam-policy-binding $projectId `
        --member="serviceAccount:$serviceAccount" `
        --role="$role" `
        --condition=None `
        --quiet 2>$null
}

Write-Host ""
Write-Host "✓ Enabling required APIs..." -ForegroundColor Green

$apis = @(
    "aiplatform.googleapis.com",
    "generativelanguage.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "  Enabling $api..." -ForegroundColor White
    gcloud services enable $api --quiet 2>$null
}

Write-Host ""
Write-Host "✓ Redeploying backend with updated configuration..." -ForegroundColor Green
Write-Host ""

# Redeploy backend
gcloud run deploy $backendService `
    --image="gcr.io/$projectId/${backendService}:latest" `
    --platform=managed `
    --region=$region `
    --allow-unauthenticated `
    --port=8000 `
    --cpu=2 `
    --memory=4Gi `
    --max-instances=10 `
    --min-instances=1 `
    --service-account="$serviceAccount" `
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$projectId,DEBUG=false,USE_VERTEX_AI=true" `
    --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║   ✅ Fix Applied Successfully!                             ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend URL: https://$backendService-$projectNumber.$region.run.app"
    Write-Host "API Docs:    https://$backendService-$projectNumber.$region.run.app/docs"
    Write-Host ""
    Write-Host "✓ The 403 authentication scope error should now be resolved."
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Deployment failed. Check the logs above." -ForegroundColor Red
    exit 1
}
