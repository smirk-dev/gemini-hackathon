# LegalMind Deployment Troubleshooting Guide

## Issue: 403 - ACCESS_TOKEN_SCOPE_INSUFFICIENT

### Symptoms
```
Error: 403 Request had insufficient authentication scopes.
[reason: "ACCESS_TOKEN_SCOPE_INSUFFICIENT"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
```

### Root Cause
Your service account on Cloud Run is missing the required IAM role to access Vertex AI. When `USE_VERTEX_AI=true`, the backend needs the `roles/aiplatform.user` permission.

### Solution

#### Quick Fix (Recommended)

**For Windows (PowerShell):**
```powershell
.\fix-vertex-ai-permissions.ps1 -ProjectId "legalmind-486106"
```

**For Linux/Mac (Bash):**
```bash
chmod +x fix-vertex-ai-permissions.sh
./fix-vertex-ai-permissions.sh legalmind-486106
```

#### Manual Fix

If the scripts don't work, run these commands directly:

1. **Enable required APIs:**
   ```bash
   gcloud services enable aiplatform.googleapis.com --project=legalmind-486106
   gcloud services enable generativeai.googleapis.com --project=legalmind-486106
   ```

2. **Grant Vertex AI User role:**
   ```bash
   gcloud projects add-iam-policy-binding legalmind-486106 \
     --member="serviceAccount:legalmind-backend@legalmind-486106.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

3. **Restart your Cloud Run service:**
   ```bash
   gcloud run services update legalmind-backend \
     --region=us-central1 \
     --update-env-vars="USE_VERTEX_AI=true"
   ```

---

## Issue: Backend Not Always Active

### Symptoms
- Backend goes offline after a period of inactivity
- App becomes inaccessible
- Cloud Run service shows "inactive"

### Root Causes
1. **Cold starts**: Cloud Run scales to zero when inactive
2. **Memory issues**: Container using too much memory (crashes on startup)
3. **Startup timeout**: Initialization taking too long
4. **Lifespan issues**: Improper async handling in startup/shutdown

### Solutions

#### 1. Reduce Cold Start Time

Update `Dockerfile` to use Python 3.11 slim (already done):
```dockerfile
FROM python:3.11-slim
```

#### 2. Fix Startup Issues

The backend uses async initialization that can timeout. Check `backend/api/app_new.py`:

**Current settings in `main_new.py`:**
```python
port = int(os.environ.get("PORT", 8000))
uvicorn.run(
    "api.app_new:app",
    host="0.0.0.0",
    port=port,
    reload=False,  # Never use reload=True in production!
    log_level="warning",
)
```

#### 3. Add Health Check Endpoint

Cloud Run needs a health check. Your API should expose a `/health` endpoint:

The endpoint should be added to `backend/api/endpoints_new.py`:
```python
@router.get("/health", tags=["Health"])
async def health():
    """Health check endpoint for Cloud Run."""
    return {
        "status": "ok",
        "service": "legalmind-backend",
        "timestamp": datetime.utcnow().isoformat()
    }
```

#### 4. Update Cloud Run Deployment

Add health check configuration:
```bash
gcloud run deploy legalmind-backend \
  --image gcr.io/legalmind-486106/legalmind-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --http2 \
  --timeout 60 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 1 \
  --health-startup-port 8000 \
  --health-startup-initial-delay 120 \
  --health-startup-timeout 30 \
  --health-startup-failure-threshold 5
```

Key parameters:
- `--min-instances 1`: Keep at least 1 instance warm to prevent cold starts
- `--memory 1Gi`: Allocate enough memory
- `--cpu 1`: Allocate enough CPU
- `--health-startup-*`: Configure Startup Health Check

---

## Issue: App Not Accessible

### Symptoms
- Frontend gets connection refused
- API returns 503 or connection timeout
- Backend URL returns no response

### Diagnostics

1. **Check service status:**
   ```bash
   gcloud run services describe legalmind-backend --region=us-central1
   ```

2. **Check logs:**
   ```bash
   gcloud run services logs read legalmind-backend --region=us-central1 --limit=50
   ```

3. **Test endpoint directly:**
   ```bash
   curl https://legalmind-backend-<id>.us-central1.run.app/health
   ```

4. **Check CORS settings:**
   Ensure `ALLOWED_ORIGINS` includes your frontend URL:
   ```bash
   gcloud run services update legalmind-backend \
     --set-env-vars="ALLOWED_ORIGINS=https://legalmind-frontend-<id>.us-central1.run.app"
   ```

### Common Fixes

1. **Increase timeout:**
   ```bash
   gcloud run deploy legalmind-backend --timeout 60
   ```

2. **Increase memory:**
   ```bash
   gcloud run deploy legalmind-backend --memory 1Gi
   ```

3. **Check CORS configuration** in `backend/api/app_new.py`:
   ```python
   origins = settings.allowed_origins.split(",")
   app.add_middleware(
       CORSMiddleware,
       allow_origins=origins if settings.allowed_origins else ["*"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

## Deployment Checklist

- [ ] Service account has `roles/aiplatform.user` role
- [ ] APIs enabled: `aiplatform.googleapis.com`, `generativeai.googleapis.com`
- [ ] Environment variable: `USE_VERTEX_AI=true`
- [ ] Environment variable: `GOOGLE_CLOUD_PROJECT=legalmind-486106`
- [ ] Health check endpoint available at `/health`
- [ ] `--min-instances 1` set on Cloud Run
- [ ] `--memory 1Gi` or higher allocated
- [ ] `--timeout 60` or higher set
- [ ] CORS configured for frontend URL
- [ ] Logs checked for startup errors

---

## Quick Redeploy

```bash
# Build locally
docker build -t gcr.io/legalmind-486106/legalmind-backend:latest .

# Push to registry
docker push gcr.io/legalmind-486106/legalmind-backend:latest

# Deploy to Cloud Run with proper config
gcloud run deploy legalmind-backend \
  --image gcr.io/legalmind-486106/legalmind-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 60 \
  --min-instances 1 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=legalmind-486106,USE_VERTEX_AI=true,DEBUG=false"
```

---

## Monitoring

### View Real-time Logs
```bash
gcloud run services logs read legalmind-backend --region us-central1 --follow
```

### Check Service Metrics
```bash
gcloud run services describe legalmind-backend --region=us-central1
```

### Check Error Rate
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=legalmind-backend" \
  --limit=50 \
  --format=json
```

---

## Need More Help?

1. Check logs: `gcloud run services logs read legalmind-backend --limit=100`
2. Verify permissions: `gcloud projects get-iam-policy legalmind-486106 --filter="members:legalmind-backend@legalmind-486106.iam.gserviceaccount.com"`
3. Test locally first: `python backend/main_new.py`
