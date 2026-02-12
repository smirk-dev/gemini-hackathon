#!/usr/bin/env pwsh

# LegalMind Frontend Deployment Script
# Deploys updated frontend to Cloud Run

$projectId = "legalmind-486106"
$region = "us-central1"
$serviceName = "legalmind-frontend"
$image = "gcr.io/$projectId/$serviceName"

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   LegalMind Frontend Deployment - Cloud Run                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "ℹ️  Configuration:" -ForegroundColor White
Write-Host "   Project:  $projectId"
Write-Host "   Region:   $region"
Write-Host "   Service:  $serviceName"
Write-Host "   Image:    $image"
Write-Host ""

# Check prerequisites
Write-Host "✓ Checking prerequisites..." -ForegroundColor Green
$checks = @(
    @{ cmd = "gcloud"; name = "Google Cloud CLI" },
    @{ cmd = "docker"; name = "Docker" }
)

foreach ($check in $checks) {
    if (Get-Command $check.cmd -ErrorAction SilentlyContinue) {
        Write-Host "  ✅ $($check.name) found" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($check.name) not found" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Set Google Cloud project
Write-Host "✓ Setting Google Cloud project..." -ForegroundColor Green
gcloud config set project $projectId --quiet
Write-Host ""

# Build Docker image using Cloud Build
Write-Host "✓ Building Docker image with Cloud Build..." -ForegroundColor Green
Write-Host ""

$buildCmd = @(
    "builds",
    "submit",
    "--tag=$image`:latest",
    "--timeout=30m",
    "--verbosity=info",
    "."
)

gcloud @buildCmd
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ Build completed successfully" -ForegroundColor Green
Write-Host ""

# Deploy to Cloud Run
Write-Host "✓ Deploying to Cloud Run..." -ForegroundColor Green
Write-Host ""

$deployCmd = @(
    "run",
    "deploy",
    $serviceName,
    "--image=$image`:latest",
    "--platform=managed",
    "--region=$region",
    "--allow-unauthenticated",
    "--port=3000",
    "--cpu=2",
    "--memory=2Gi",
    "--max-instances=10",
    "--min-instances=1",
    "--set-env-vars=NEXT_PUBLIC_API_URL=https://legalmind-backend-677928716377.us-central1.run.app",
    "--quiet"
)

gcloud @deployCmd
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host ""

# Get service URL
Write-Host "✓ Retrieving service URL..." -ForegroundColor Green
$serviceUrl = gcloud run services describe $serviceName --region=$region --format='value(status.url)'

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Deployment Complete ✅                                   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend URL: $serviceUrl"
Write-Host "Backend URL:  https://legalmind-backend-677928716377.us-central1.run.app"
Write-Host ""
Write-Host "📊 Next Steps:"
Write-Host "  1. Visit the frontend URL above"
Write-Host "  2. Test the chat interface"
Write-Host "  3. Upload a contract for analysis"
Write-Host "  4. Monitor logs: gcloud run logs read $serviceName --region=$region"
Write-Host ""
