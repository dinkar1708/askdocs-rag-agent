# Security Documentation

Security guidelines and best practices for askdocs-rag-agent.

---

## Overview

This directory contains comprehensive security documentation covering all aspects of building and deploying askdocs-rag-agent securely.

**Current Security Status:** 🟡 DEVELOPMENT - Security hardening in progress

**Target for Production:** 🟢 SECURE - All critical vulnerabilities addressed

---

## Security Documents

| Document | Purpose | Audience |
|---|---|---|
| [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) | **Start here** - Security requirements checklist | Everyone |
| [API_SECURITY.md](API_SECURITY.md) | API endpoint security & authentication | Developers |
| [SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md) | API keys & secrets handling | DevOps, Developers |

---

## Quick Security Guide

### Before You Start Development

✅ **Read first:**
1. [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) - Know what to implement
2. [SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md) - Never commit secrets

### During Development

✅ **For each feature:**
1. Check relevant security doc (API, Auth, Data)
2. Follow secure coding patterns
3. Test security controls

### Before Deployment

✅ **Must complete:**
1. Review [../deployment/](../deployment/) security sections
2. Complete [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)
3. Run security tests

---

## Security Priorities

### 🔴 Critical (Must Have Before Production)

- [ ] API key authentication implemented
- [ ] Rate limiting on all endpoints
- [ ] HTTPS enforcement
- [ ] Secrets stored in vault (not .env in production)
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (using ORM)
- [ ] No sensitive data in logs
- [ ] CORS properly configured

### 🟡 High Priority (Recommended)

- [ ] Multi-tenant data isolation
- [ ] Audit logging
- [ ] Security headers (HSTS, CSP, etc.)
- [ ] Token expiration and refresh
- [ ] Database connection encryption
- [ ] Regular security dependency updates

### 🟢 Medium Priority (Good to Have)

- [ ] Penetration testing
- [ ] Security monitoring and alerts
- [ ] Automated vulnerability scanning
- [ ] MFA for admin access

---

## Security by Component

### API Layer
**Threats:** Unauthorized access, DDoS, injection attacks

**Mitigations:**
- API key authentication → [API_SECURITY.md](API_SECURITY.md)
- Rate limiting → [API_SECURITY.md](API_SECURITY.md)
- Input validation → [API_SECURITY.md](API_SECURITY.md)

### Database Layer
**Threats:** SQL injection, unauthorized data access, data leaks

**Mitigations:**
- SQLAlchemy ORM (prevents SQL injection)
- Connection encryption (TLS)
- Row-level security (multi-tenant)

### LLM Integration
**Threats:** Prompt injection, API key leakage, data exfiltration

**Mitigations:**
- Input sanitization → [API_SECURITY.md](API_SECURITY.md)
- API key in secrets vault → [SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md)
- Response validation → [API_SECURITY.md](API_SECURITY.md)

### Document Storage
**Threats:** Unauthorized document access, data leaks

**Mitigations:**
- Tenant isolation (database design)
- Access control checks → [API_SECURITY.md](API_SECURITY.md)
- Secure deletion

---

## OWASP Top 10 Coverage

| Risk | Status | Mitigation |
|---|---|---|
| A01: Broken Access Control | 🟢 COVERED | Row-level security, API keys |
| A02: Cryptographic Failures | 🟡 PARTIAL | TLS required, pgvector encryption |
| A03: Injection | 🟢 COVERED | SQLAlchemy ORM, input validation |
| A04: Insecure Design | 🟡 IN PROGRESS | Security checklist, reviews |
| A05: Security Misconfiguration | 🟡 IN PROGRESS | Deployment security docs |
| A06: Vulnerable Components | 🟡 ONGOING | Dependency updates required |
| A07: Authentication Failures | 🟡 PARTIAL | API keys, rate limiting needed |
| A08: Data Integrity Failures | 🟢 COVERED | ORM prevents tampering |
| A09: Logging Failures | 🔴 TODO | Audit logging needed |
| A10: SSRF | 🟡 PARTIAL | LLM API calls need validation |

---

## Security Testing Checklist

### Manual Testing

```bash
# 1. Test rate limiting
for i in {1..200}; do curl http://localhost:8000/ask; done
# Should see 429 after limit

# 2. Test authentication
curl http://localhost:8000/documents  # Should fail without API key
curl -H "X-API-Key: invalid" http://localhost:8000/documents  # Should fail

# 3. Test input validation
curl -X POST http://localhost:8000/ask -d '{"question": "<script>alert(1)</script>"}'
# Should sanitize or reject

# 4. Test SQL injection (should fail)
curl -X POST http://localhost:8000/ask -d '{"question": "1; DROP TABLE documents;"}'
# Should be safe (ORM prevents)
```

### Automated Testing

```bash
# Security dependency check
pip install safety
safety check

# Secrets scan
pip install detect-secrets
detect-secrets scan

# SAST (Static Application Security Testing)
pip install bandit
bandit -r app/
```

---

## Incident Response

**If a security issue is discovered:**

1. **DO NOT** discuss publicly
2. Report to: security@yourdomain.com
3. Include: affected component, severity, steps to reproduce
4. Follow disclosure guidelines

---

## Security Resources

### Internal
- [Security Checklist](SECURITY_CHECKLIST.md) - Implementation guide
- [Deployment Security](../deployment/) - Production hardening

### External
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [GCP Security Best Practices](https://cloud.google.com/security/best-practices)

---

## Security Review Schedule

### Pre-Development
- [x] Review security requirements
- [ ] Threat modeling session

### During Development
- [ ] Weekly security checklist review
- [ ] Code reviews with security focus

### Pre-Deployment
- [ ] Complete security checklist
- [ ] Penetration testing
- [ ] Security audit

### Post-Deployment
- [ ] Monthly dependency updates
- [ ] Quarterly security reviews
- [ ] Annual penetration testing

---

## Contact

**Security Issues:** Open a private security advisory on GitHub
**Questions:** See individual security documents
**Updates:** Track security TODOs in project board

---

## Version

**Last Updated:** 2026-07-20
**Status:** Initial documentation - implementation in progress
