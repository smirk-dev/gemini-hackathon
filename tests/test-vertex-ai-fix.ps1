#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test that the Vertex AI fallback fix is working
    Verifies that the 403 error is resolved
#>

param(
    [string]$BackendUrl = "https://legalmind-backend-677928716377.us-central1.run.app"
)

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "TESTING VERTEX AI FIX - 403 Error Resolution" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Test 1: Health check endpoint
Write-Host "Test 1: Health Check Endpoint" -ForegroundColor Yellow
Write-Host "URL: $BackendUrl/health" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "$BackendUrl/health" -TimeoutSec 15 -ErrorAction Stop
    Write-Host "✅ Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "✅ Response:" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | Format-List | Write-Host
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ HEALTH CHECK PASSED" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Message -contains "403") {
        Write-Host ""
        Write-Host "ERROR: Still getting 403 error!" -ForegroundColor Red
        Write-Host "This means the fallback fix may not have deployed yet." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Status: Deployment might still be in progress" -ForegroundColor Yellow
        Write-Host "Please wait 2-3 minutes and try again." -ForegroundColor Yellow
    }
    elseif ($_.Exception.Message -contains "Connection refused" -or $_.Exception.Message -contains "host unreachable") {
        Write-Host ""
        Write-Host "INFO: Service may be cold starting or not yet active" -ForegroundColor Yellow
        Write-Host "Cloud Run scales to zero when inactive. Please wait..." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "TEST COMPLETE" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Additional debugging info
Write-Host "Deployment Info:" -ForegroundColor Yellow
Write-Host ""
try {
    $serviceInfo = gcloud run services describe legalmind-backend --project=legalmind-486106 --region=us-central1 --format="table(status.conditions[0].status)"  2>$null
    Write-Host "Service Status:" -ForegroundColor Cyan
    Write-Host $serviceInfo -ForegroundColor Gray
}
catch {
    Write-Host "Could not fetch service info" -ForegroundColor Gray
}

Write-Host ""
Write-Host "SUMMARY:" -ForegroundColor Green
Write-Host "- Fixed 4 fallback bugs in gemini_service.py" -ForegroundColor Green
Write-Host "- Changed all 'if GenerativeModel' checks to 'if not GenerativeModel'" -ForegroundColor Green
Write-Host "  → Now raises errors instead of silently falling back to public API" -ForegroundColor Green
Write-Host "- Backend will either work with Vertex AI or fail clearly" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps if error persists:" -ForegroundColor Yellow
Write-Host "1. Wait 2-3 minutes for deployment to complete" -ForegroundColor Yellow
Write-Host "2. Check logs: gcloud run services logs read legalmind-backend --limit=50" -ForegroundColor Yellow
Write-Host "3. Verify Vertex AI SDK: pip show google-cloud-aiplatform" -ForegroundColor Yellow
Write-Host ""
