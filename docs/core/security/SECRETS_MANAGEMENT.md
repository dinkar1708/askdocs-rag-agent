# Secrets Management Guide

How to securely handle API keys, tokens, and sensitive configuration.

---

## Overview

**Golden Rule:** Never commit secrets to git. Ever.

---

## What Are Secrets?

Secrets are sensitive values that must be protected:

- API keys (Gemini, Azure OpenAI, etc.)
- Database passwords
- JWT secret keys
- Encryption keys
- OAuth client secrets
- Service account credentials

---

## Local Development

### Using .env Files

```bash
# .env (NEVER commit this file)
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXX
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/askdocs
SECRET_KEY=dev-secret-key-change-in-production
```

**Setup:**
```bash
# 1. Copy template
cp .env.example .env

# 2. Fill in your secrets
# Edit .env with your actual values

# 3. Verify .gitignore
grep ".env" .gitignore  # Should show .env is ignored
```

### .env.example Template

```bash
# .env.example (Safe to commit - no real secrets)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/askdocs
SECRET_KEY=change-this-in-production
```

---

## Production Secrets Management

### GCP Secret Manager (Recommended for GCP)

**Store secrets:**
```bash
# Create secret
echo "AIzaSyXXXXXXXXXXXXXX" | gcloud secrets create gemini-api-key \
  --data-file=-

# Create database URL
echo "postgresql://user:pass@/db?host=/cloudsql/proj:region:instance" \
  | gcloud secrets create database-url \
  --data-file=-
```

**Access in Cloud Run:**
```bash
gcloud run deploy askdocs-api \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
  --set-secrets="DATABASE_URL=database-url:latest"
```

**In code:**
```python
# app/core/config.py
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Injected by Cloud Run
```

---

### Azure Key Vault (For Azure deployments)

**Store secrets:**
```bash
# Create Key Vault
az keyvault create \
  --name askdocs-vault \
  --resource-group askdocs-rg

# Add secrets
az keyvault secret set \
  --vault-name askdocs-vault \
  --name gemini-api-key \
  --value "AIzaSyXXXXXXXXXX"

az keyvault secret set \
  --vault-name askdocs-vault \
  --name database-url \
  --value "postgresql://..."
```

**Access in Container Apps:**
```bash
az containerapp create \
  --name askdocs-api \
  --secrets \
    "gemini-key=keyvaultref:https://askdocs-vault.vault.azure.net/secrets/gemini-api-key" \
    "db-url=keyvaultref:https://askdocs-vault.vault.azure.net/secrets/database-url" \
  --env-vars \
    "GEMINI_API_KEY=secretref:gemini-key" \
    "DATABASE_URL=secretref:db-url"
```

---

## Secrets Rotation

### Why Rotate?

- Limit damage if a key is compromised
- Comply with security policies
- Best practice for production systems

### How Often?

| Secret Type | Rotation Frequency |
|---|---|
| API keys | Every 90 days |
| Database passwords | Every 180 days |
| JWT secret keys | Every 365 days |
| Service account keys | Every 90 days |

### Rotation Process

**Example: Rotate Gemini API Key**

```bash
# 1. Generate new key in Google AI Studio
# https://aistudio.google.com/app/apikey

# 2. Update secret in vault
gcloud secrets versions add gemini-api-key \
  --data-file=- <<< "NEW_API_KEY_HERE"

# 3. Deploy with new secret (Cloud Run auto-picks latest version)
gcloud run services update askdocs-api

# 4. Verify new key works
curl https://askdocs-api-xxx.run.app/health

# 5. Delete old key from Google AI Studio
```

---

## Never Do This ❌

### Hardcoded Secrets

```python
# ❌ WRONG - Never hardcode secrets
GEMINI_API_KEY = "AIzaSyXXXXXXXXXXXX"
DATABASE_URL = "postgresql://user:mypassword@db.com/askdocs"
```

### Committing .env

```bash
# ❌ WRONG - Never commit .env
git add .env
git commit -m "Add configuration"
```

### Secrets in Code Comments

```python
# ❌ WRONG - No secrets in comments
# My API key: AIzaSyXXXXXXXXXXXX
def get_api_key():
    pass
```

### Secrets in Logs

```python
# ❌ WRONG - Never log secrets
logger.info(f"Using API key: {GEMINI_API_KEY}")

# ✅ CORRECT - Mask secrets
logger.info(f"Using API key: {GEMINI_API_KEY[:8]}...")
```

---

## Do This Instead ✅

### Load from Environment

```python
# ✅ CORRECT - Load from environment
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
```

### Use Secrets Vault

```python
# ✅ CORRECT - Production secrets from vault
# Cloud Run/Container Apps inject secrets as env vars
# No code changes needed!
```

### Validate on Startup

```python
# app/main.py
@app.on_event("startup")
def validate_secrets():
    required_secrets = [
        "GEMINI_API_KEY",
        "DATABASE_URL",
        "SECRET_KEY"
    ]

    missing = [s for s in required_secrets if not os.getenv(s)]
    if missing:
        raise ValueError(f"Missing secrets: {missing}")

    logger.info("All required secrets validated")
```

---

## Detecting Leaked Secrets

### Pre-commit Hook

Install `detect-secrets`:

```bash
pip install detect-secrets

# Scan repository
detect-secrets scan

# If secrets found:
detect-secrets audit .secrets.baseline
```

### GitHub Secret Scanning

GitHub automatically scans for leaked secrets. If detected:
1. You'll get an email alert
2. Rotate the leaked secret immediately
3. Review how it was leaked
4. Add to `.gitignore` if not already there

---

## Emergency: Secret Leaked

**If you accidentally commit a secret:**

### 1. Immediately Rotate the Secret

```bash
# Generate new API key
# Delete old API key from provider
# Update secret in vault
```

### 2. Remove from Git History

```bash
# ⚠️ WARNING: This rewrites git history
# Coordinate with team first

# Use BFG Repo-Cleaner
java -jar bfg.jar --replace-text passwords.txt repo.git

# Or git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (dangerous!)
git push origin --force --all
```

### 3. Notify

- Inform your team
- Report to security team
- Update incident log

---

## Multi-Environment Secrets

### Development

```bash
# .env.dev
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=postgresql://postgres:postgres@localhost/askdocs_dev
SECRET_KEY=dev-key-not-for-production
```

### Staging

```bash
# Secrets in GCP Secret Manager
# Prefix: staging-*
staging-gemini-api-key
staging-database-url
staging-secret-key
```

### Production

```bash
# Secrets in GCP Secret Manager
# Prefix: prod-*
prod-gemini-api-key
prod-database-url
prod-secret-key
```

**Load based on environment:**
```python
# app/core/config.py
import os

ENV = os.getenv("ENVIRONMENT", "dev")  # dev, staging, prod

if ENV == "prod":
    # Secrets from vault (injected by Cloud Run)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
elif ENV == "dev":
    # Local .env file
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

---

## Secrets Checklist

### Setup

- [ ] `.env` file in `.gitignore`
- [ ] `.env.example` committed (no real secrets)
- [ ] `detect-secrets` installed
- [ ] Pre-commit hook configured

### Development

- [ ] All secrets in `.env` file
- [ ] No secrets in source code
- [ ] No secrets in logs
- [ ] Secrets validated on startup

### Production

- [ ] All secrets in vault (GCP Secret Manager / Azure Key Vault)
- [ ] Secrets injected as environment variables
- [ ] Rotation schedule documented
- [ ] Access logs enabled on vault

### Team

- [ ] Team trained on secrets management
- [ ] Incident response plan documented
- [ ] Regular secrets audits scheduled

---

## Tools & Resources

### Tools

- **detect-secrets** - Scan repo for secrets
- **git-secrets** - Prevent committing secrets
- **gitleaks** - Detect secrets in git history

### Services

- **GCP Secret Manager** - https://cloud.google.com/secret-manager
- **Azure Key Vault** - https://azure.microsoft.com/en-us/services/key-vault/
- **AWS Secrets Manager** - https://aws.amazon.com/secrets-manager/

### Documentation

- [12-Factor App: Config](https://12factor.net/config)
- [OWASP Secrets Management](https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password)

---

## Next Steps

1. **Set up local development** - Create `.env` from `.env.example`
2. **Configure vault** - Set up GCP Secret Manager or Azure Key Vault
3. **Test secret loading** - Verify secrets load correctly
4. **Document secrets** - Update `CONFIGURATION.md` with required secrets
5. **Set rotation reminders** - Calendar reminders for key rotation

---

**Remember:** When in doubt, don't commit it. Secrets should never be in source control.
