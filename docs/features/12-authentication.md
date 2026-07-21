# Authentication & Authorization

**Status:** 🔴 Not Implemented (Planned)

User authentication and authorization system for secure access control.

---

## Overview

**Purpose:** Secure the AskDocs system with user authentication and role-based access control.

**Current State:**
- APIs are currently open (no authentication required)
- All users can access all documents
- No user management or session tracking

**Target State:**
- User login with email/password
- JWT-based authentication
- Role-based access control (Admin, User, Viewer)
- User-specific document collections
- API key authentication for integrations

---

## Problem Statement

**Without Authentication:**
- ❌ Anyone can upload/delete documents
- ❌ No data privacy or separation
- ❌ Cannot track who asked what
- ❌ Not suitable for multi-user deployments
- ❌ Security risk in production

**With Authentication:**
- ✅ Secure access control
- ✅ User-specific document collections
- ✅ Audit trail (who did what)
- ✅ Multi-tenant support
- ✅ Production-ready security

---

## Proposed Solution

### Authentication Methods

**1. Email/Password (Primary)**
```
POST /auth/register
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe"
}

POST /auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}
→ Returns JWT token
```

**2. API Keys (For Integrations)**
```
GET /documents
Headers:
  X-API-Key: sk_live_abc123...
```

**3. OAuth (Future)**
- Google Sign-In
- Microsoft SSO
- GitHub OAuth

---

## User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access: manage users, all documents, system settings |
| **User** | Upload documents, ask questions, manage own documents |
| **Viewer** | Read-only: ask questions, view documents (no upload/delete) |
| **API User** | Programmatic access via API keys |

---

## Implementation Plan

### Phase 1: Basic Auth (Backend)

**Database Schema:**
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  role VARCHAR(50) DEFAULT 'user',
  created_at TIMESTAMP,
  last_login TIMESTAMP
);

CREATE TABLE api_keys (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  key_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  created_at TIMESTAMP,
  expires_at TIMESTAMP
);

-- Add user_id to documents table
ALTER TABLE documents ADD COLUMN user_id UUID REFERENCES users(id);

-- Add user_id to sessions table (for chat history)
ALTER TABLE sessions ADD COLUMN user_id INTEGER REFERENCES users(id);
-- nullable=True for backward compatibility with anonymous sessions
```

**Backend APIs:**
- `POST /auth/register` - Create new user
- `POST /auth/login` - Login and get JWT token
- `POST /auth/logout` - Invalidate token
- `GET /auth/me` - Get current user info
- `POST /auth/refresh` - Refresh JWT token

**Dependencies:**
```python
# requirements.txt
python-jose[cryptography]  # JWT tokens
passlib[bcrypt]            # Password hashing
python-multipart           # Form data
```

**FastAPI Middleware:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    # Verify JWT token
    # Return user object or raise 401
    pass

# Protect endpoints
@router.post("/documents")
async def upload_document(
    file: UploadFile,
    current_user: User = Depends(get_current_user)
):
    # Only authenticated users can upload
    pass
```

### Phase 2: Web UI Integration

**Login Page:**
- Email/password form
- "Remember me" checkbox
- Password reset link
- Social login buttons (future)

**State Management:**
```typescript
// composables/useAuth.ts
export const useAuth = () => {
  const user = useState('user', () => null)
  const token = useState('token', () => null)

  const login = async (email: string, password: string) => {
    const response = await $fetch('/auth/login', {
      method: 'POST',
      body: { email, password }
    })
    token.value = response.access_token
    user.value = response.user
    // Store in localStorage/cookie
  }

  const logout = () => {
    token.value = null
    user.value = null
    // Clear storage
  }

  return { user, token, login, logout }
}
```

**Protected Routes:**
```vue
<!-- middleware/auth.ts -->
export default defineNuxtRouteMiddleware((to, from) => {
  const { token } = useAuth()

  if (!token.value && to.path !== '/login') {
    return navigateTo('/login')
  }
})
```

### Phase 3: Advanced Features

**Multi-tenancy:**
- Organizations/workspaces
- Team document sharing
- Role-based permissions per workspace

**SSO Integration:**
- SAML 2.0 support
- Azure AD / Okta integration
- Google Workspace integration

**Audit Logging:**
- Track all user actions
- Document access logs
- Query history per user

---

## API Changes

### Before (No Auth)
```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@document.pdf"
```

### After (With Auth)
```bash
curl -X POST http://localhost:8000/documents \
  -H "Authorization: Bearer eyJhbGc..." \
  -F "file=@document.pdf"
```

---

## Session Management with Authentication

### Current Implementation (v1.0 - Anonymous Sessions)

**Status:** ✅ Implemented

Sessions are stored in localStorage without user authentication:
- Session ID stored in browser localStorage
- Anyone with session_id can access the chat history
- No login required

```typescript
// Frontend: localStorage stores session
localStorage.setItem('askdocs_session_id', '123')

// Backend: No user ownership check
GET /sessions/123  // Returns session if exists
```

### Future Implementation (v2.0 - User-Owned Sessions)

**Status:** 🔴 Planned

Sessions will be linked to authenticated users:

**Backend Changes:**
```python
# Create session linked to user
@router.post("/sessions/")
async def create_session(
    current_user: User = Depends(get_current_user)
):
    session = Session(user_id=current_user.id)
    db.add(session)
    db.commit()
    return session

# Get session (verify ownership)
@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id  # Ownership check
    ).first()

    if not session:
        raise HTTPException(404, "Session not found")

    return session
```

**Frontend Changes:**
```typescript
// Store JWT token + session_id
const token = localStorage.getItem('jwt_token')
const sessionId = localStorage.getItem('session_id')

// Send token in all requests
await $fetch('/sessions/123', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

### Migration Strategy

**Option 1: Backward Compatible (Recommended)**
- Keep `user_id` nullable in sessions table
- `user_id = NULL` → Anonymous session (current behavior)
- `user_id = X` → User-owned session (after login)
- Existing anonymous sessions continue working

**Option 2: Require Login**
- Make `user_id` required
- All existing sessions become invalid
- Users must login to create new sessions

### Session Lifecycle Comparison

| Feature | Anonymous (Current) | Authenticated (Planned) |
|---------|-------------------|----------------------|
| **Create Session** | No auth required | Requires login |
| **Access Session** | Anyone with ID | Only session owner |
| **List Sessions** | Not available | User's sessions only |
| **Persist Across Devices** | ❌ No (localStorage) | ✅ Yes (server-side) |
| **Privacy** | ⚠️ Public if ID known | ✅ Private per user |
| **Multi-device Sync** | ❌ No | ✅ Yes |

### Implementation Effort

**Low Effort (2-3 days):**
- ✅ Add `user_id` column to sessions
- ✅ Modify session creation endpoint
- ✅ Add ownership checks to session access
- ✅ Update frontend to send JWT token

**Medium Effort (1 week):**
- Add full authentication system (register/login/logout)
- Frontend login UI
- Token refresh logic
- Migration script for existing sessions

---

---

## Security Considerations

**Password Security:**
- ✅ Bcrypt hashing (cost factor 12)
- ✅ Minimum 8 characters, complexity rules
- ✅ Rate limiting on login attempts
- ✅ Account lockout after failed attempts

**Token Security:**
- ✅ JWT with RS256 signing
- ✅ Short expiry (15 minutes access, 7 days refresh)
- ✅ Token rotation on refresh
- ✅ Revocation list for logout

**API Key Security:**
- ✅ Hashed storage (never plain text)
- ✅ Prefix for identification (sk_live_...)
- ✅ Rate limiting per key
- ✅ Expiration dates

---

## Migration Strategy

**For Existing Deployments:**

1. **Add auth tables** (migrations)
2. **Create default admin user**
3. **Enable auth middleware** (opt-in flag)
4. **Migrate existing documents** to admin user
5. **Update clients** to use tokens
6. **Enforce auth** (remove flag)

**Environment Variable:**
```bash
# .env
ENABLE_AUTH=true
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

---

## Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| Phase 1 | Backend auth APIs, database schema | 1 week |
| Phase 2 | Web UI login/signup, protected routes | 3 days |
| Phase 3 | Multi-tenancy, SSO, audit logs | 2 weeks |

**Total:** ~3-4 weeks

---

## Testing Checklist

- [ ] User registration with email validation
- [ ] Login with correct/incorrect credentials
- [ ] JWT token expiration and refresh
- [ ] Protected endpoints reject unauthorized requests
- [ ] Password reset flow
- [ ] API key creation and usage
- [ ] Role-based access control
- [ ] Multi-tenant data isolation
- [ ] Rate limiting on auth endpoints
- [ ] CSRF protection

---

## Related Features

- **Multi-tenant Support** - Requires auth foundation
- **Audit Logs** - Track authenticated user actions
- **Document Sharing** - Share documents between users
- **Team Workspaces** - Collaborative document collections

---

## Resources

**FastAPI Security:**
- https://fastapi.tiangolo.com/tutorial/security/
- https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/

**JWT Best Practices:**
- https://tools.ietf.org/html/rfc7519
- https://auth0.com/docs/secure/tokens/json-web-tokens

**Nuxt Auth:**
- https://nuxt.com/modules/auth
- https://sidebase.io/nuxt-auth/

---

**Status:** Planned for future release
**Priority:** High (required for production deployments)
**Dependencies:** None
**Blocks:** Multi-tenancy, team features, enterprise deployment
