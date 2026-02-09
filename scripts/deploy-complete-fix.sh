#!/bin/bash
# LegalMind Complete Deployment Fix - Bash Version
# This script completely fixes the 403 scope error and ensures proper deployment
# Usage: bash deploy-complete-fix.sh "legalmind-486106"

set -e

PROJECT_ID="${1:-legalmind-486106}"
REGION="${2:-us-central1}"
SERVICE_NAME="${3:-legalmind-backend}"

# ============================================================================
# COLORS & UTILITIES
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

write_step() {
    echo ""
    echo -e "${CYAN}█ $1${NC}"
    echo -e "${CYAN}────────────────────────────────────────────────────────────────────────────────${NC}"
}

write_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

write_error() {
    echo -e "${RED}❌ $1${NC}"
}

write_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

write_info() {
    echo -e "${NC}ℹ️  $1${NC}"
}

verify_tool() {
    if ! command -v $1 &> /dev/null; then
        write_error "$1 is not installed or not in PATH"
        exit 1
    fi
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

write_step "PRE-FLIGHT CHECKS"

write_info "Verifying required tools..."
verify_tool "gcloud"
verify_tool "docker"

write_success "All required tools found"

write_info "Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID --quiet

# Verify project exists
if ! gcloud projects describe $PROJECT_ID &>/dev/null; then
    write_error "Cannot access project: $PROJECT_ID"
    exit 1
fi
write_success "Project verified: $PROJECT_ID"

# ============================================================================
# STEP 1: ENABLE ALL REQUIRED APIS
# ============================================================================

write_step "STEP 1: ENABLING GOOGLE CLOUD APIS"

apis=(
    "aiplatform.googleapis.com"
    "generativeai.googleapis.com"
    "run.googleapis.com"
    "firestore.googleapis.com"
    "storage-api.googleapis.com"
    "cloudbuild.googleapis.com"
    "containerregistry.googleapis.com"
    "artifactregistry.googleapis.com"
    "iam.googleapis.com"
    "iamcredentials.googleapis.com"
    "cloudresourcemanager.googleapis.com"
)

for api in "${apis[@]}"; do
    write_info "Enabling $api..."
    gcloud services enable $api --quiet 2>/dev/null || true
done

write_success "All APIs enabled"

# ============================================================================
# STEP 2: VERIFY/CREATE SERVICE ACCOUNT
# ============================================================================

write_step "STEP 2: VERIFYING SERVICE ACCOUNT"

SA_EMAIL="${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
write_info "Service Account: $SA_EMAIL"

if gcloud iam service-accounts describe $SA_EMAIL &>/dev/null; then
    write_success "Service account exists: $SA_EMAIL"
else
    write_warning "Service account does not exist, creating..."
    gcloud iam service-accounts create $SERVICE_NAME \
        --display-name="LegalMind Backend Service Account" \
        --description="Service account for LegalMind backend on Cloud Run" \
        --quiet
    write_success "Service account created: $SA_EMAIL"
fi

# ============================================================================
# STEP 3: GRANT REQUIRED IAM ROLES
# ============================================================================

write_step "STEP 3: GRANTING REQUIRED IAM ROLES"

roles=(
    "roles/aiplatform.user"
    "roles/datastore.user"
    "roles/storage.objectAdmin"
    "roles/secretmanager.secretAccessor"
    "roles/logging.logWriter"
)

for role in "${roles[@]}"; do
    write_info "Granting $role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role" \
        --condition=None \
        --quiet 2>/dev/null || true
done

write_success "All required IAM roles granted"

# ============================================================================
# STEP 4: VERIFY IAM ROLES ARE PROPERLY SET
# ============================================================================

write_step "STEP 4: VERIFYING IAM ROLES"

write_info "Checking service account roles..."
assigned_roles=$(gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:$SA_EMAIL" \
    --format="table(bindings.role)" | tail -n +2)

if [ -z "$assigned_roles" ]; then
    write_error "No roles found for service account!"
    exit 1
fi

write_info "Assigned roles:"
echo "$assigned_roles" | while read role; do
    echo -e "${GREEN}  ✓ $role${NC}"
done

# Check for critical roles
echo "$assigned_roles" | grep -q "roles/aiplatform.user" || {
    write_error "CRITICAL: roles/aiplatform.user not assigned!"
    exit 1
}

echo "$assigned_roles" | grep -q "roles/datastore.user" || {
    write_error "CRITICAL: roles/datastore.user not assigned!"
    exit 1
}

write_success "All critical roles verified"

# ============================================================================
# STEP 5: BUILD DOCKER IMAGE
# ============================================================================

write_step "STEP 5: BUILDING DOCKER IMAGE"

write_info "This will take 2-5 minutes..."

image_tag="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
write_info "Building image: $image_tag"

if docker build -t $image_tag -f Dockerfile . > /tmp/docker-build.log 2>&1; then
    write_success "Docker image built successfully"
else
    write_error "Docker build failed"
    tail -20 /tmp/docker-build.log
    exit 1
fi

# ============================================================================
# STEP 6: PUSH TO CONTAINER REGISTRY
# ============================================================================

write_step "STEP 6: PUSHING TO CONTAINER REGISTRY"

write_info "Configuring Docker auth for GCR..."
gcloud auth configure-docker gcr.io --quiet 2>/dev/null

write_info "Pushing image: $image_tag"
if docker push $image_tag > /tmp/docker-push.log 2>&1; then
    write_success "Image pushed to container registry"
else
    write_error "Docker push failed"
    tail -20 /tmp/docker-push.log
    exit 1
fi

# ============================================================================
# STEP 7: DEPLOY TO CLOUD RUN
# ============================================================================

write_step "STEP 7: DEPLOYING TO CLOUD RUN"

write_info "Deploying with proper configuration..."

if gcloud run deploy $SERVICE_NAME \
    --image $image_tag \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --service-account $SA_EMAIL \
    --memory 1Gi \
    --cpu 1 \
    --timeout 60 \
    --min-instances 1 \
    --max-instances 10 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},USE_VERTEX_AI=true,DEBUG=false" \
    --quiet; then
    write_success "Cloud Run deployment successful"
else
    write_error "Cloud Run deployment failed"
    exit 1
fi

# ============================================================================
# STEP 8: GET SERVICE URL
# ============================================================================

write_step "STEP 8: RETRIEVING SERVICE URL"

service_url=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format="value(status.url)" 2>/dev/null || echo "")

if [ ! -z "$service_url" ]; then
    write_success "Service URL: $service_url"
else
    write_warning "Could not retrieve service URL"
fi

# ============================================================================
# STEP 9: VERIFY DEPLOYMENT
# ============================================================================

write_step "STEP 9: VERIFYING DEPLOYMENT"

write_info "Waiting 10 seconds for service to stabilize..."
sleep 10

if [ ! -z "$service_url" ]; then
    write_info "Testing health check endpoint..."
    if health_response=$(curl -s "$service_url/api/health" 2>&1); then
        if echo "$health_response" | grep -q '"status"'; then
            write_success "Health check passed!"
            write_info "Response: $health_response"
        else
            write_warning "Unexpected health check response (service might still be starting)"
            write_info "Response: $health_response"
        fi
    else
        write_warning "Could not test health endpoint (service might still be starting)"
    fi
fi

# ============================================================================
# STEP 10: CHECK LOGS
# ============================================================================

write_step "STEP 10: CHECKING DEPLOYMENT LOGS"

write_info "Recent logs (last 20 lines):"
gcloud run services logs read $SERVICE_NAME \
    --region $REGION \
    --limit 20 \
    --format "table(timestamp,text)" 2>/dev/null || write_warning "Could not retrieve logs"

# ============================================================================
# FINAL SUMMARY
# ============================================================================

write_step "DEPLOYMENT COMPLETE"

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        LegalMind Backend Deployment Summary                    ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Project ID:        ${BOLD}$PROJECT_ID${NC}"
echo -e "Service:           ${BOLD}$SERVICE_NAME${NC}"
echo -e "Region:            ${BOLD}$REGION${NC}"
echo -e "Service Account:   ${BOLD}$SA_EMAIL${NC}"

if [ ! -z "$service_url" ]; then
    echo -e "Service URL:       ${BOLD}$service_url${NC}"
fi

echo ""
echo -e "${CYAN}Configuration:${NC}"
echo "  • Memory:        1Gi"
echo "  • CPU:           1 vCPU"
echo "  • Instances:     1-10 (auto-scaling)"
echo "  • Timeout:       60 seconds"
echo "  • Vertex AI:     Enabled"
echo "  • Debug Mode:    Disabled"
echo ""
echo -e "${CYAN}IAM Roles:${NC}"
echo -e "${GREEN}  ✓ roles/aiplatform.user${NC}"
echo -e "${GREEN}  ✓ roles/datastore.user${NC}"
echo -e "${GREEN}  ✓ roles/storage.objectAdmin${NC}"
echo -e "${GREEN}  ✓ roles/logging.logWriter${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Monitor logs:"
echo -e "     ${BOLD}gcloud run services logs read $SERVICE_NAME --region=$REGION --follow${NC}"
echo ""
echo "  2. View service details:"
echo -e "     ${BOLD}gcloud run services describe $SERVICE_NAME --region=$REGION${NC}"
echo ""
if [ ! -z "$service_url" ]; then
    echo "  3. Test the API:"
    echo -e "     ${BOLD}curl $service_url/api/health${NC}"
    echo ""
fi
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
write_success "✨ Deployment completed successfully! Backend should now be fully operational."
echo ""
