# GCP Deployment Guide

Deploy askdocs-rag-agent to Google Cloud Platform using Cloud Run.

---

## Architecture

```
GitHub
  ↓ (push to main)
GitHub Actions
  ↓ (build image)
Artifact Registry
  ↓ (deploy)
Cloud Run
  ↓ (connect)
Cloud SQL (PostgreSQL + pgvector)
  ↓ (LLM calls)
Gemini API / Vertex AI
```

---

## Prerequisites

- GCP account with billing enabled
- `gcloud` CLI installed
- Project created (e.g., `askdocs-prod`)

---

## One-Time Setup

### 1. Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com
```

### 2. Set Variables

```bash
export PROJECT_ID=askdocs-prod
export REGION=us-central1
export SERVICE_NAME=askdocs-api
export DB_INSTANCE=askdocs-db
```

---

## Deploy Database

### Create Cloud SQL Instance

```bash
gcloud sql instances create $DB_INSTANCE \
  --project=$PROJECT_ID \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --database-flags=cloudsql.enable_pgvector=on \
  --backup \
  --backup-start-time=03:00
```

**Cost:** ~$7/month for db-f1-micro

### Create Database

```bash
gcloud sql databases create askdocs \
  --instance=$DB_INSTANCE
```

### Set Password

```bash
gcloud sql users set-password postgres \
  --instance=$DB_INSTANCE \
  --password=$(openssl rand -base64 32)
```

**Save password to Secret Manager:**
```bash
echo "your_password" | gcloud secrets create db-password --data-file=-
```

### Enable pgvector Extension

```bash
gcloud sql connect $DB_INSTANCE --user=postgres
# In psql:
\c askdocs
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

---

## Build and Deploy API

### Create Artifact Registry

```bash
gcloud artifacts repositories create askdocs \
  --repository-format=docker \
  --location=$REGION \
  --description="askdocs-rag-agent images"
```

### Build Image

```bash
gcloud builds submit \
  --tag $REGION-docker.pkg.dev/$PROJECT_ID/askdocs/api:latest \
  --project=$PROJECT_ID
```

### Store Secrets

```bash
# Gemini API key
echo "your_gemini_key" | gcloud secrets create gemini-api-key --data-file=-

# Database URL
gcloud sql instances describe $DB_INSTANCE --format='value(connectionName)'
# Output: askdocs-prod:us-central1:askdocs-db

# Create secret
echo "postgresql://postgres:PASSWORD@/askdocs?host=/cloudsql/askdocs-prod:us-central1:askdocs-db" \
  | gcloud secrets create database-url --data-file=-
```

### Deploy to Cloud Run

```bash
gcloud run deploy $SERVICE_NAME \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/askdocs/api:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest,DATABASE_URL=database-url:latest" \
  --set-env-vars="LLM_PROVIDER=gemini,CONFIDENCE_THRESHOLD=0.7" \
  --add-cloudsql-instances $PROJECT_ID:$REGION:$DB_INSTANCE \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 0 \
  --timeout 300
```

**Service URL:** https://askdocs-api-xxx-uc.a.run.app

---

## Run Migrations

```bash
# Option 1: Cloud Run Jobs
gcloud run jobs create askdocs-migrate \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/askdocs/api:latest \
  --command="alembic" \
  --args="upgrade,head" \
  --region=$REGION \
  --set-secrets="DATABASE_URL=database-url:latest" \
  --add-cloudsql-instances $PROJECT_ID:$REGION:$DB_INSTANCE

gcloud run jobs execute askdocs-migrate --region=$REGION

# Option 2: Cloud Shell proxy
cloud_sql_proxy -instances=$PROJECT_ID:$REGION:$DB_INSTANCE=tcp:5432 &
alembic upgrade head
```

---

## Verify Deployment

```bash
# Get service URL
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format='value(status.url)'

# Health check
curl https://askdocs-api-xxx-uc.a.run.app/health

# Upload test document
curl -X POST https://askdocs-api-xxx-uc.a.run.app/documents \
  -F "file=@samples/handbook.pdf"
```

---

## CI/CD with GitHub Actions

**File:** `.github/workflows/deploy-gcp.yml`

```yaml
name: Deploy to GCP

on:
  push:
    branches: [main]

env:
  PROJECT_ID: askdocs-prod
  REGION: us-central1
  SERVICE_NAME: askdocs-api

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Build and push
        run: |
          gcloud builds submit \
            --tag ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/askdocs/api:${{ github.sha }}

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ${{ env.SERVICE_NAME }} \
            --image ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/askdocs/api:${{ github.sha }} \
            --region ${{ env.REGION }}
```

**Setup Workload Identity Federation:**
```bash
# See: https://github.com/google-github-actions/auth
```

---

## Monitoring

### View Logs

```bash
gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=50
```

### Metrics

Cloud Console → Cloud Run → askdocs-api → Metrics

**Key metrics:**
- Request count
- Latency (p50, p95, p99)
- Error rate
- Instance count

### Alerts

```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05
```

---

## Scaling

### Auto-scaling

Cloud Run auto-scales based on:
- Request concurrency (default: 80)
- CPU/memory usage

**Configure:**
```bash
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --concurrency=50 \
  --min-instances=1 \
  --max-instances=20
```

### Database Scaling

**Upgrade tier:**
```bash
gcloud sql instances patch $DB_INSTANCE \
  --tier=db-g1-small  # 1.7 GB RAM (~$25/month)
```

**Read replicas (future):**
```bash
gcloud sql instances create $DB_INSTANCE-replica \
  --master-instance-name=$DB_INSTANCE \
  --region=$REGION
```

---

## Cost Optimization

### Current Estimate

| Resource | Tier | Monthly Cost |
|---|---|---|
| Cloud Run | 1M req, 1 vCPU | $0-10 |
| Cloud SQL | db-f1-micro | $7 |
| Gemini API | 1M tokens (free tier) | $0 |
| Artifact Registry | <10 GB | $1 |
| **Total** | | **$8-18/month** |

### Optimization Tips

**1. Scale to zero:**
```bash
--min-instances=0  # Default, costs nothing when idle
```

**2. Use cheaper database tier:**
```bash
--tier=db-f1-micro  # Smallest tier
```

**3. Use free tier Gemini API:**
- 15 RPM, 1M tokens/day
- Upgrade to paid only when needed

**4. Set budget alerts:**
```bash
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="askdocs-budget" \
  --budget-amount=50USD
```

---

## Security

### API Authentication

**Add API key middleware:**
```python
# app/api/middleware.py
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in VALID_KEYS:
        raise HTTPException(401)
```

**Store keys in Secret Manager:**
```bash
echo "key1,key2,key3" | gcloud secrets create api-keys --data-file=-

gcloud run services update $SERVICE_NAME \
  --set-secrets="API_KEYS=api-keys:latest"
```

### Network Security

**VPC Connector (optional):**
```bash
gcloud compute networks vpc-access connectors create askdocs-connector \
  --region=$REGION \
  --range=10.8.0.0/28

gcloud run services update $SERVICE_NAME \
  --vpc-connector=askdocs-connector \
  --vpc-egress=private-ranges-only
```

---

## Troubleshooting

### Cold Start Latency

**Problem:** First request takes >5s

**Solutions:**
- Keep 1 min instance: `--min-instances=1`
- Optimize container size (multi-stage Docker build)
- Use startup CPU boost: `--cpu-boost` (preview)

### Database Connection Timeout

**Problem:** Cloud SQL connection fails

**Solution:**
```bash
# Verify connection name
gcloud sql instances describe $DB_INSTANCE --format='value(connectionName)'

# Ensure it's added to Cloud Run
gcloud run services update $SERVICE_NAME \
  --add-cloudsql-instances PROJECT:REGION:INSTANCE
```

### Out of Memory

**Problem:** Container crashes with OOM

**Solution:**
```bash
# Increase memory
gcloud run services update $SERVICE_NAME --memory=2Gi

# Or optimize embedding model (use smaller model)
```

---

## Rollback

```bash
# List revisions
gcloud run revisions list --service=$SERVICE_NAME --region=$REGION

# Rollback to previous
gcloud run services update-traffic $SERVICE_NAME \
  --region=$REGION \
  --to-revisions=askdocs-api-00002-abc=100
```

---

## Clean Up

```bash
# Delete Cloud Run service
gcloud run services delete $SERVICE_NAME --region=$REGION

# Delete Cloud SQL instance
gcloud sql instances delete $DB_INSTANCE

# Delete Artifact Registry repo
gcloud artifacts repositories delete askdocs --location=$REGION
```

---

**Next:** See [DEPLOYMENT.md](../../docs/DEPLOYMENT.md) for Azure deployment.
