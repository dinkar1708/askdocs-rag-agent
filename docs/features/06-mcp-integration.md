# Feature: MCP Integration

**What:** Expose document search and Q&A as Model Context Protocol (MCP) tools for AI assistants.

**Why it matters:** Use your document library directly in Claude Desktop, Gemini CLI, or any MCP-compatible tool.

---

## User Story

```
As a knowledge worker,
I want to ask Claude Desktop questions about my company's internal docs,
So I can get answers without leaving my AI assistant.
```

---

## What is MCP?

**Model Context Protocol** is a standard that lets AI assistants use external tools.

**Think of it like:**
- Plugins for ChatGPT
- Extensions for VS Code
- But standardized across all AI assistants

**With MCP, Claude Desktop can:**
- Search your askdocs database
- Ask grounded questions
- Get cited answers
- All without you switching to Swagger UI

---

## MCP Tools Exposed

### 1. search_documents

**What it does:** Raw vector search (for debugging or custom workflows).

**When to use:**
- "Find all mentions of 'remote work' in my docs"
- "Show me chunks about vacation policy"

**Example in Claude Desktop:**
```
You: Find all mentions of parental leave in my handbook

Claude: I'll search your documents.
[Uses search_documents(query="parental leave", top_k=5)]

Claude: I found 5 relevant chunks:
1. handbook.pdf, page 23: "Employees are entitled to 12 weeks..."
2. handbook.pdf, page 24: "Parental leave can be taken..."
...
```

---

### 2. ask_question

**What it does:** Full RAG pipeline with grounded answer + citations.

**When to use:**
- "What is the vacation policy?"
- "How do I request parental leave?"

**Example in Claude Desktop:**
```
You: What's our company's remote work policy?

Claude: I'll search your documents using the askdocs tool.
[Uses ask_question(question="What is the remote work policy?")]

Claude: According to your employee handbook (page 15):
"Employees may work remotely up to 2 days per week with manager approval.
Full-time remote work requires VP approval."

Sources: handbook.pdf, page 15
```

---

## Setup with Claude Desktop

### Step 1: Start askdocs Service

```bash
cd askdocs-rag-agent
docker compose up
```

The MCP server runs alongside the REST API.

---

### Step 2: Configure Claude Desktop

**Edit config file:**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Add:**
```json
{
  "mcpServers": {
    "askdocs": {
      "command": "docker",
      "args": [
        "compose",
        "exec",
        "-T",
        "api",
        "python",
        "-m",
        "app.mcp.server"
      ],
      "cwd": "/Users/yourname/Documents/askdocs-rag-agent"
    }
  }
}
```

**Or, if running locally without Docker:**
```json
{
  "mcpServers": {
    "askdocs": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "cwd": "/path/to/askdocs-rag-agent",
      "env": {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/askdocs",
        "LLM_PROVIDER": "gemini",
        "GEMINI_API_KEY": "your_key_here"
      }
    }
  }
}
```

---

### Step 3: Restart Claude Desktop

Quit and reopen Claude Desktop completely.

**Verify:** Tools should appear in the tool menu (hammer icon).

---

### Step 4: Upload Documents

**Via REST API (askdocs doesn't expose upload via MCP yet):**
```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@employee-handbook.pdf"
```

---

### Step 5: Ask Questions in Claude Desktop

```
You: What's our vacation policy?

Claude: I'll check your documents using the askdocs tool.
[Uses ask_question internally]

Claude: According to your employee handbook (page 7):
"Employees receive 15 days of paid vacation per year..."
```

---

## Real-World Workflows

### Workflow 1: Research Across Documents

```
You: Compare the vacation policies in all my uploaded documents

Claude:
[Uses search_documents(query="vacation policy", top_k=20)]

Claude: I found vacation policies in 3 documents:
1. handbook-2025.pdf: 15 days per year
2. handbook-2026.pdf: 18 days per year (updated!)
3. contractor-agreement.pdf: No vacation (contractors only)

The policy increased from 15 to 18 days in 2026.
```

---

### Workflow 2: Answering Client Questions

```
You: A customer asks: "Can I return a damaged item after 30 days?"

Claude:
[Uses ask_question(question="Can damaged items be returned after 30 days?")]

Claude: According to your terms.pdf (page 5):
"Items damaged during shipping can be returned within 60 days."

So yes, damaged items have a 60-day return window, not 30.

Would you like me to draft a response to the customer?
```

---

### Workflow 3: Compliance Check

```
You: Does our employee handbook comply with California labor laws regarding sick leave?

Claude:
[Uses ask_question(question="What is the sick leave policy?")]

Claude: Your handbook (page 9) states:
"Employees receive 10 days of paid sick leave per year."

However, California law requires at least 40 hours (5 days) per year.
Your policy exceeds the minimum, so you're compliant.

Sources: handbook.pdf, page 9
```

---

## How It Works Behind the Scenes

### MCP Protocol Flow

```
Claude Desktop
    ↓ (user asks question)
MCP Client (in Claude)
    ↓ (calls tool: ask_question)
MCP Server (app/mcp/server.py)
    ↓ (runs RAG pipeline)
PostgreSQL (retrieves chunks)
    ↓
LLM Provider (generates answer)
    ↓
MCP Server (returns answer + citations)
    ↓
Claude Desktop (shows to user)
```

---

### MCP Server Code

**File:** `app/mcp/server.py`

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("askdocs")

@app.list_tools()
async def list_tools():
    return [
        {
            "name": "search_documents",
            "description": "Vector search for document chunks",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "number", "default": 5}
                },
                "required": ["query"]
            }
        },
        {
            "name": "ask_question",
            "description": "Ask grounded question with citations",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"}
                },
                "required": ["question"]
            }
        }
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_documents":
        return search_documents(**arguments)
    elif name == "ask_question":
        return ask_question(**arguments)

if __name__ == "__main__":
    stdio_server(app)
```

---

## Troubleshooting

### Tools don't appear in Claude Desktop

**Check:**
1. Config file is valid JSON
2. `cwd` path is correct (full path, not relative)
3. Claude Desktop fully restarted (Quit → Reopen)

**View logs:**
```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp-server-askdocs.log
```

---

### "Database connection failed" error

**Fix:** Add `DATABASE_URL` to env vars in config:

```json
{
  "mcpServers": {
    "askdocs": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "env": {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/askdocs"
      }
    }
  }
}
```

---

### Slow responses

**Cause:** Embedding model loads on first query (cold start).

**Fix:** Keep MCP server running in background:
```bash
# Start server separately
python -m app.mcp.server &

# Update config to connect to running server (future enhancement)
```

---

## Security Considerations

**MCP tools run with full database access.**

**For production:**
- Add API key authentication
- Scope tools to specific tenants
- Log all MCP tool calls

**Example:**
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict, context: dict):
    # Extract API key from context
    api_key = context.get("api_key")
    if not verify_api_key(api_key):
        raise PermissionError("Invalid API key")

    # Scope to tenant
    tenant_id = get_tenant_from_key(api_key)
    return ask_question(arguments["question"], tenant_id=tenant_id)
```

---

## Limitations & Future Plans

**Current limitations:**
- No document upload via MCP (must use REST API)
- No session/chat history (single-turn only)
- No streaming responses

**Future enhancements:**
- [ ] `upload_document` MCP tool
- [ ] `list_documents` MCP tool
- [ ] Multi-turn chat via MCP
- [ ] Streaming responses

---

## Next Steps

→ [API Reference](../docs/API.md) - REST API for document upload
→ [MCP Docs](../docs/MCP.md) - Detailed MCP setup guide
