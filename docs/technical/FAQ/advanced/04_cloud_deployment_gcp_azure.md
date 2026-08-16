# Advanced Level: Cloud Deployment (GCP & Azure)

---

## 1. Google Cloud Platform (GCP) Deployment

### Q1: How is AskDocs deployed to GCP Cloud Run?
**Answer:**
AskDocs is containerized and runs as a serverless service on **GCP Cloud Run** paired with **GCP Cloud SQL** (PostgreSQL with pgvector):

```
User ──► Cloud Load Balancer ──► Cloud Run (FastAPI Container)
                                       │
                                       ├─► Cloud SQL (PostgreSQL 15 + pgvector)
                                       └─► Google Gemini API (LLM Generation)
```

**Deployment Steps:**
```bash
# 1. Build and push container to Google Artifact Registry
docker build -t gcr.io/$PROJECT_ID/askdocs-api:latest .
docker push gcr.io/$PROJECT_ID/askdocs-api:latest

# 2. Deploy to Cloud Run with environment variables
gcloud run deploy askdocs-api \
  --image gcr.io/$PROJECT_ID/askdocs-api:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=$DB_URL,LLM_PROVIDER=gemini,GEMINI_API_KEY=$GEMINI_KEY
```

---

## 2. Azure Container Apps Deployment

### Q2: How can it be deployed on Microsoft Azure?
**Answer:**
On Azure, AskDocs uses **Azure Container Apps** and **Azure Database for PostgreSQL - Flexible Server** with pgvector enabled:
```bash
# Enable pgvector in Azure Flexible Server
az postgres flexible-server parameter set \
  --resource-group rg-askdocs \
  --server-name askdocs-pg \
  --name azure.extensions \
  --value "VECTOR"
```
Container Apps scales from 0 to N replicas automatically and integrates with Azure OpenAI deployments.
