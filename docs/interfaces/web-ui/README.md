# Web UI Documentation

Simple web interface for AskDocs.

---

## Overview

**Two purposes:**

1. **Demo** - Show product to prospects
2. **Client Use** - Simple interface for non-technical users

**Access:** http://localhost:8000 (after deployment: https://your-domain.com)

---

## Features

**Upload Documents**
- Drag & drop PDF files
- See upload progress
- View uploaded documents list

**Ask Questions**
- Type question in natural language
- Get instant answers with citations
- Click citation to see source page

**Document Management**
- List all uploaded documents
- View document details (pages, chunks)
- Delete documents

**Multi-turn Chat**
- Conversation history
- Follow-up questions
- Clear chat option

---

## Interface Design

### Main Page Layout

```
┌─────────────────────────────────────────────┐
│  AskDocs                        [My Docs]   │
├─────────────────────────────────────────────┤
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  Ask a question about your documents  │ │
│  │  [Type here...]                   [→] │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  Or upload a new document:                  │
│  ┌───────────────────────────────────────┐ │
│  │  Drag & drop PDF or [Browse Files]    │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  Recent Questions:                          │
│  • What is the vacation policy?             │
│  • How many sick days?                      │
│  • What is the refund policy?               │
│                                             │
└─────────────────────────────────────────────┘
```

### Answer Display

```
┌─────────────────────────────────────────────┐
│  Q: What is the vacation policy?            │
├─────────────────────────────────────────────┤
│  A: Employees receive 15 days of paid       │
│     vacation per year.                      │
│                                             │
│  Sources:                                   │
│  📄 handbook.pdf, page 7 [View]             │
│                                             │
│  [👍 Helpful] [👎 Not Helpful]              │
└─────────────────────────────────────────────┘
```

### Documents Page

```
┌─────────────────────────────────────────────┐
│  My Documents                    [+ Upload] │
├─────────────────────────────────────────────┤
│  📄 handbook.pdf                            │
│     42 pages, 156 chunks                    │
│     Uploaded: 2026-07-20                    │
│     [Delete]                                │
│                                             │
│  📄 terms.pdf                               │
│     15 pages, 58 chunks                     │
│     Uploaded: 2026-07-19                    │
│     [Delete]                                │
│                                             │
└─────────────────────────────────────────────┘
```

---

## User Flows

### Flow 1: First Time User

1. Open web UI
2. See empty state: "Upload your first document"
3. Drag & drop PDF
4. Wait for processing (progress bar)
5. See success: "handbook.pdf uploaded (42 pages)"
6. Ask first question
7. Get answer with citation

**Time:** 2-3 minutes

---

### Flow 2: Regular User

1. Open web UI
2. See recent questions
3. Click recent question → see previous answer
4. OR ask new question
5. Get answer instantly

**Time:** 30 seconds

---

### Flow 3: Document Management

1. Click "My Docs" button
2. See all uploaded documents
3. Click document → view details
4. Delete old document
5. Upload new version

**Time:** 1 minute

---

## Technical Implementation

### Tech Stack

**Frontend:**
- HTML5, CSS3, JavaScript (vanilla - no frameworks)
- Optional: React/Vue for richer UI

**Backend:**
- FastAPI serves both API and static files
- `/` → Web UI (index.html)
- `/api/*` → REST API endpoints
- `/docs` → Swagger UI (for developers)

### File Structure

```
app/
├── static/
│   ├── index.html       # Main page
│   ├── style.css        # Styling
│   ├── app.js           # JavaScript
│   └── assets/
│       └── logo.svg
├── templates/           # (optional for Jinja2)
└── api/
    └── routes.py        # API endpoints
```

### API Integration

**JavaScript example:**

```javascript
// Upload document
async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/documents', {
    method: 'POST',
    body: formData
  });

  return await response.json();
}

// Ask question
async function askQuestion(question) {
  const response = await fetch('/api/ask', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question})
  });

  return await response.json();
}
```

---

## Deployment

### Local Development

```bash
# Start server
docker compose up

# Open browser
http://localhost:8000
```

### Production

**Option 1: Same domain**
- Web UI: https://askdocs.ai
- API: https://askdocs.ai/api

**Option 2: Separate domains**
- Web UI: https://app.askdocs.ai
- API: https://api.askdocs.ai

**Option 3: Subdirectory**
- Web UI: https://company.com/askdocs
- API: https://company.com/askdocs/api

---

## Security

**Authentication:**
- Login with email/password
- Session cookies
- API key stored in local storage

**HTTPS:**
- Required for production
- Certificate via Let's Encrypt

**CORS:**
- Allow web UI domain only
- No open CORS in production

---

## Customization

**For clients, customize:**

1. **Branding**
   - Logo
   - Colors
   - Company name

2. **Features**
   - Hide document upload (admin-only)
   - Add user management
   - Custom landing page

3. **Integration**
   - SSO login
   - Embed in existing portal
   - White-label option

---

## Demo Script

**For sales demo (5 minutes):**

### Step 1: Show Clean UI (30 sec)
"This is the AskDocs interface. Clean, simple, works on any device."

### Step 2: Upload Document (1 min)
"Let me upload our employee handbook..." [drag & drop]
"Processing... 42 pages indexed in 15 seconds."

### Step 3: Ask Question (1 min)
"What is the vacation policy?" [type, enter]
"Instant answer with exact page citation. Click to verify source."

### Step 4: Show Grounding (1 min)
"Now let me ask something NOT in the document..."
"What's the weather today?" [type, enter]
"See? It says 'not_found' - no hallucinations."

### Step 5: Show Features (1 min)
"You can also see all documents, delete old ones, chat history..."

### Step 6: Close (30 sec)
"Questions? Want to try with your documents?"

---

## Client Benefits

**Why clients want web UI:**

1. **Easy Onboarding**
   - No API knowledge needed
   - Just open browser

2. **Self-Service**
   - Upload documents themselves
   - Manage their knowledge base

3. **Mobile Friendly**
   - Works on phone/tablet
   - Responsive design

4. **Familiar Interface**
   - Like ChatGPT, but grounded
   - No learning curve

---

## Analytics (Optional)

**Track usage:**
- Questions asked/day
- Most common questions
- Documents uploaded
- User satisfaction (thumbs up/down)

**Dashboard for admins:**
- Usage metrics
- Popular documents
- Question trends
- Performance stats

---

## Implementation Roadmap

**Basic UI**
- Upload + Ask interface
- Citation display
- Document list

**Enhanced Features**
- Multi-turn chat
- Search history
- Better styling

**Advanced Features**
- User accounts
- Analytics dashboard
- Admin panel

---

**Related Docs:**
- [API Reference](../../core/architecture/API.md)
- [Features](../../features/)
- [Deployment](../../core/deployment/)
