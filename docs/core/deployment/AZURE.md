# Azure Deployment Guide

Deploy askdocs-rag-agent to Azure using Container Apps.

---

## Architecture

```
GitHub
  ↓ (push to main)
GitHub Actions
  ↓ (build image)
Azure Container Registry
  ↓ (deploy)
Azure Container Apps
  ↓ (connect)
Azure Database for PostgreSQL
  ↓ (LLM calls)
Azure OpenAI
```

---

## Prerequisites

- Azure account with active subscription
- Azure CLI installed (`az`)
- Resource group created

---

## Quick Setup

```bash
# Login
az login

# Set variables
RESOURCE_GROUP=askdocs-rg
LOCATION=eastus
APP_NAME=askdocs-api
DB_NAME=askdocs-db
ACR_NAME=askdocsacr
```

---

## 1. Create PostgreSQL Database

```bash
# Create Flexible Server
az postgres flexible-server create \
  --name $DB_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user postgres \
  --admin-password $(openssl rand -base64 32) \
  --sku-name Standard_B1ms \
  --version 15 \
  --storage-size 32 \
  --public-access 0.0.0.0

# Enable pgvector
az postgres flexible-server parameter set \
  --name azure.extensions \
  --value VECTOR \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_NAME

# Create database
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_NAME \
  --database-name askdocs

# Enable pgvector (connect and run)
az postgres flexible-server connect \
  --name $DB_NAME \
  --admin-user postgres
# In psql:
\c askdocs
CREATE EXTENSION IF NOT EXISTS vector;
```

**Cost:** ~$15/month (B1ms tier)

---

## 2. Create Container Registry

```bash
az acr create \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku Basic \
  --admin-enabled true
```

---

## 3. Build and Push Image

```bash
# Build
az acr build \
  --registry $ACR_NAME \
  --image askdocs-api:latest \
  --file Dockerfile \
  .

# Or push from local
docker build -t $ACR_NAME.azurecr.io/askdocs-api:latest .
az acr login --name $ACR_NAME
docker push $ACR_NAME.azurecr.io/askdocs-api:latest
```

---

## 4. Create Azure OpenAI Resource

```bash
az cognitiveservices account create \
  --name askdocs-openai \
  --resource-group $RESOURCE_GROUP \
  --location eastus \
  --kind OpenAI \
  --sku S0

# Deploy a model
az cognitiveservices account deployment create \
  --name askdocs-openai \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard
```

---

## 5. Deploy Container App

```bash
# Create Container Apps environment
az containerapp env create \
  --name askdocs-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Get ACR credentials
ACR_PASSWORD=$(az acr credential show \
  --name $ACR_NAME \
  --query passwords[0].value -o tsv)

# Get database connection string
DB_HOST=$(az postgres flexible-server show \
  --name $DB_NAME \
  --resource-group $RESOURCE_GROUP \
  --query fullyQualifiedDomainName -o tsv)

# Deploy app
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment askdocs-env \
  --image $ACR_NAME.azurecr.io/askdocs-api:latest \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_NAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 10 \
  --cpu 1 \
  --memory 2Gi \
  --secrets \
    "openai-key=YOUR_AZURE_OPENAI_KEY" \
    "db-password=YOUR_DB_PASSWORD" \
  --env-vars \
    "LLM_PROVIDER=azure_openai" \
    "AZURE_OPENAI_ENDPOINT=https://askdocs-openai.openai.azure.com/" \
    "AZURE_OPENAI_DEPLOYMENT=gpt-4" \
    "AZURE_OPENAI_KEY=secretref:openai-key" \
    "DATABASE_URL=secretref:db-url"
```

**App URL:** https://askdocs-api.xxx.azurecontainerapps.io

---

## 6. Run Migrations

```bash
# Option 1: Container Apps Job
az containerapp job create \
  --name askdocs-migrate \
  --resource-group $RESOURCE_GROUP \
  --environment askdocs-env \
  --image $ACR_NAME.azurecr.io/askdocs-api:latest \
  --command "/bin/sh" \
  --args "-c,alembic upgrade head" \
  --secrets "db-url=YOUR_CONNECTION_STRING" \
  --env-vars "DATABASE_URL=secretref:db-url"

az containerapp job start --name askdocs-migrate --resource-group $RESOURCE_GROUP
```

---

## CI/CD with GitHub Actions

**File:** `.github/workflows/deploy-azure.yml`

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

env:
  AZURE_CONTAINER_APP: askdocs-api
  RESOURCE_GROUP: askdocs-rg
  ACR_NAME: askdocsacr

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Build and push
        run: |
          az acr build \
            --registry ${{ env.ACR_NAME }} \
            --image askdocs-api:${{ github.sha }} \
            .

      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --name ${{ env.AZURE_CONTAINER_APP }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --image ${{ env.ACR_NAME }}.azurecr.io/askdocs-api:${{ github.sha }}
```

---

## Monitoring

```bash
# View logs
az containerapp logs show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --tail 50

# Metrics in Azure Portal
# Container Apps → askdocs-api → Metrics
```

---

## Cost Estimate

| Resource | Tier | Monthly Cost |
|---|---|---|
| Container Apps | 1M requests | $10-20 |
| PostgreSQL Flexible | B1ms | $15 |
| Azure OpenAI | Pay-per-token | Variable |
| Container Registry | Basic | $5 |
| **Total** | | **$30-40/month** |

---

## Clean Up

```bash
az group delete --name $RESOURCE_GROUP --yes
```

---

**For more details, see [DEPLOYMENT.md](../../docs/DEPLOYMENT.md)**
