# Deployment Guide

Production deployment paths for GCP (detailed) and Azure (brief overview).

---

## Overview

The service is a **stateless container + PostgreSQL**, deployable anywhere that runs Docker.

**Recommended stack:**
- **Container runtime:** Cloud Run (GCP) or Azure Container Apps
- **Database:** Cloud SQL (GCP) or Azure Database for PostgreSQL
- **LLM:** Gemini/Vertex AI (GCP) or Azure OpenAI
- **CI/CD:** GitHub Actions

---

## GCP Deployment (Primary)

Google Cloud Run is the default target: cheap, scales to zero, generous free tier.

### Architecture

```
GitHub → Actions → Artifact Registry → Cloud Run ← Cloud SQL
                                         ↓
                                    Gemini API
```

### Prerequisites

- GCP account with billing enabled
- `gcloud` CLI installed
- Project created (e.g., `askdocs-prod`)

### Step-by-Step Deployment

#### 1. Set Up Cloud SQL (PostgreSQL)

```bash
# Set variables
PROJECT_ID=askdocs-prod
REGION=us-central1
INSTANCE_NAME=askdocs-db

# Create instance with pgvector support
gcloud sql instances create $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --database-flags=cloudsql.enable_pgvector=on

# Create database
gcloud sql databases create askdocs \
  --instance=$INSTANCE_NAME

# Set password
gcloud sql users set-password postgres \
  --instance=$INSTANCE_NAME \
  --password=YOUR_SECURE_PASSWORD
```

**Enable pgvector extension:**
```bash
# Connect via cloud shell
gcloud sql connect $INSTANCE_NAME --user=postgres

# In psql:
\c askdocs
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

#### 2. Build and Push Container

```bash
# Enable services
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# Create artifact registry
gcloud artifacts repositories create askdocs \
  --repository-format=docker \
  --location=$REGION

# Build and push
gcloud builds submit \
  --tag $REGION-docker.pkg.dev/$PROJECT_ID/askdocs/api:latest
```

#### 3. Deploy to Cloud Run

```bash
# Get Cloud SQL connection name
gcloud sql instances describe $INSTANCE_NAME --format='value(connectionName)'
# Example: askdocs-prod:us-central1:askdocs-db

# Deploy
gcloud run deploy askdocs-api \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/askdocs/api:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "LLM_PROVIDER=gemini,GEMINI_API_KEY=your_key" \
  --set-env-vars "DATABASE_URL=postgresql://postgres:PASSWORD@/askdocs?host=/cloudsql/askdocs-prod:us-central1:askdocs-db" \
  --add-cloudsql-instances askdocs-prod:us-central1:askdocs-db \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 0
```

**Service URL:** Cloud Run will output a URL like `https://askdocs-api-xxx-uc.a.run.app`

#### 4. Run Migrations

```bash
# Connect to Cloud Run instance
gcloud run services proxy askdocs-api --region $REGION

# In another terminal
curl -X POST http://localhost:8080/admin/migrate
```

Or use Cloud Run Jobs for one-time migration.

#### 5. Verify Deployment

```bash
# Health check
curl https://askdocs-api-xxx-uc.a.run.app/health

# Upload test document
curl -X POST https://askdocs-api-xxx-uc.a.run.app/documents \
  -F "file=@samples/handbook.pdf"
```

### CI/CD with GitHub Actions

`.github/workflows/deploy-gcp.yml`:

```yaml
name: Deploy to Cloud Run

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
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Build and push container
        run: |
          gcloud builds submit \
            --tag $REGION-docker.pkg.dev/$PROJECT_ID/askdocs/api:$GITHUB_SHA

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy $SERVICE_NAME \
            --image $REGION-docker.pkg.dev/$PROJECT_ID/askdocs/api:$GITHUB_SHA \
            --region $REGION \
            --platform managed
```

**Setup:**
1. Create service account with Cloud Run Admin + Cloud SQL Client roles
2. Download JSON key
3. Add as GitHub secret: `GCP_SA_KEY`

### Cost Estimate (GCP)

| Resource | Tier | Monthly Cost |
|---|---|---|
| Cloud Run | 1M requests, 1 vCPU | $0-10 (free tier covers most) |
| Cloud SQL | db-f1-micro (0.6 GB RAM) | ~$7 |
| Artifact Registry | <10 GB images | ~$1 |
| Gemini API | 1M tokens (free tier) | $0 |
| **Total** | | **~$8-18/month** |

Scale-to-zero means you only pay for active usage.

---

## Azure Deployment (Brief)

For customers requiring Azure (e.g., enterprise compliance).

### Architecture

```
GitHub → Actions → Container Registry → Container Apps ← Flexible Server
                                            ↓
                                       Azure OpenAI
```

### Quick Setup

**1. Create resources:**
```bash
RESOURCE_GROUP=askdocs-rg
LOCATION=eastus

# Resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# PostgreSQL Flexible Server
az postgres flexible-server create \
  --name askdocs-db \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user postgres \
  --admin-password YOUR_PASSWORD \
  --sku-name Standard_B1ms \
  --version 15 \
  --storage-size 32

# Enable pgvector (via extensions)
az postgres flexible-server parameter set \
  --name azure.extensions \
  --value VECTOR \
  --resource-group $RESOURCE_GROUP \
  --server-name askdocs-db

# Create database
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name askdocs-db \
  --database-name askdocs
```

**2. Deploy Container App:**
```bash
# Container Apps environment
az containerapp env create \
  --name askdocs-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Deploy app
az containerapp create \
  --name askdocs-api \
  --resource-group $RESOURCE_GROUP \
  --environment askdocs-env \
  --image ghcr.io/dinkar1708/askdocs-rag-agent:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    LLM_PROVIDER=azure_openai \
    AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/ \
    AZURE_OPENAI_KEY=secretref:openai-key \
    DATABASE_URL=secretref:db-url \
  --secrets \
    openai-key=YOUR_KEY \
    db-url=postgresql://postgres:PASSWORD@askdocs-db.postgres.database.azure.com/askdocs
```

**3. Configure Azure OpenAI:**

See Azure OpenAI setup in [Configuration](CONFIGURATION.md#azure-openai).

### Cost Estimate (Azure)

| Resource | Tier | Monthly Cost |
|---|---|---|
| Container Apps | 1M requests, 1 vCPU | ~$10-20 |
| PostgreSQL Flexible | B1ms (1 vCore, 2 GB) | ~$15 |
| Azure OpenAI | Pay-per-token | Variable |
| **Total** | | **~$25-35/month** |

---

## Kubernetes (Generic)

For self-hosted or multi-cloud deployments.

`deploy/k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: askdocs-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: askdocs-api
  template:
    metadata:
      labels:
        app: askdocs-api
    spec:
      containers:
      - name: api
        image: ghcr.io/dinkar1708/askdocs-rag-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: askdocs-secrets
              key: database-url
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: askdocs-secrets
              key: gemini-key
---
apiVersion: v1
kind: Service
metadata:
  name: askdocs-api
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: askdocs-api
```

**Deploy:**
```bash
kubectl apply -f deploy/k8s/
```

**Database:** Use managed PostgreSQL (Cloud SQL, RDS, Azure) or self-hosted with pgvector.

---

## Production Checklist

### Security
- [ ] Rotate API keys monthly
- [ ] Use secrets manager (GCP Secret Manager, Azure Key Vault)
- [ ] Enable HTTPS only (Cloud Run does this by default)
- [ ] Restrict CORS origins
- [ ] Add rate limiting (slowapi middleware)

### Performance
- [ ] Enable connection pooling (SQLAlchemy `pool_size=10`)
- [ ] Add Redis caching for identical questions
- [ ] Monitor p95 latency (set target <2s)

### Reliability
- [ ] Set up health checks (`/health` endpoint)
- [ ] Configure auto-scaling (min 1, max 10 instances)
- [ ] Enable database backups (daily)
- [ ] Add retry logic for LLM API calls

### Observability
- [ ] Structured logging to Cloud Logging / Azure Monitor
- [ ] Set up error alerting (PagerDuty, Slack)
- [ ] Track key metrics:
  - Request rate
  - "not_found" rate (should be <30%)
  - Retrieval confidence distribution

### Compliance
- [ ] Document data retention policy
- [ ] Add GDPR delete endpoint (`DELETE /users/{id}/data`)
- [ ] Log PII access (if handling sensitive docs)

---

## Rollback Procedure

**Cloud Run:**
```bash
# List revisions
gcloud run revisions list --service askdocs-api --region $REGION

# Rollback to previous
gcloud run services update-traffic askdocs-api \
  --to-revisions askdocs-api-00002-abc=100 \
  --region $REGION
```

**Azure Container Apps:**
```bash
az containerapp revision list \
  --name askdocs-api \
  --resource-group $RESOURCE_GROUP

az containerapp ingress traffic set \
  --name askdocs-api \
  --resource-group $RESOURCE_GROUP \
  --revision-weight askdocs-api--abc123=100
```

---

## Monitoring

### Cloud Run (GCP)

**Logs:**
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=askdocs-api" \
  --limit 50 \
  --format json
```

**Metrics:** Cloud Console → Cloud Run → askdocs-api → Metrics

Key metrics:
- Request count
- Request latency
- Container instance count

### Azure Container Apps

**Logs:**
```bash
az monitor log-analytics query \
  --workspace YOUR_WORKSPACE_ID \
  --analytics-query "ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'askdocs-api'"
```

**Metrics:** Azure Portal → Container Apps → askdocs-api → Metrics

---

## Troubleshooting

### Issue: Cold start latency (>5s)

**Cause:** Cloud Run spins down to zero instances.

**Fix:**
```bash
# Set min instances to 1 (costs more, but eliminates cold starts)
gcloud run services update askdocs-api \
  --min-instances 1
```

### Issue: Database connection timeout

**Cause:** Cloud SQL connection pool exhausted.

**Fix:**
```python
# app/db/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Detect stale connections
)
```

### Issue: 502 Bad Gateway

**Cause:** Container crashed or health check failed.

**Debug:**
```bash
# View logs
gcloud run services logs read askdocs-api --limit 100

# Check health endpoint
curl https://askdocs-api-xxx-uc.a.run.app/health
```

---

## Next Steps

- **Configure:** See [Configuration](CONFIGURATION.md) for environment variables
- **Monitor:** Set up alerts for errors and latency
- **Scale:** Add caching, connection pooling as traffic grows

---

**Need help?** See [GitHub Issues](https://github.com/dinkar1708/askdocs-rag-agent/issues) or reach out.
