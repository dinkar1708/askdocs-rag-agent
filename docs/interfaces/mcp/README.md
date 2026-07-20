# MCP Integration Guide

How to use askdocs-rag-agent with Model Context Protocol (MCP) compatible AI assistants.

---

## What is MCP?

**Model Context Protocol (MCP)** is a standard that allows AI assistants (Claude Desktop, Gemini CLI, etc.) to use external tools and data sources.

**With MCP, AI assistants can:**
- Search your document library directly
- Ask grounded questions and get cited answers
- Access capabilities without switching to a web UI

---

## MCP Tools Exposed

askdocs-rag-agent exposes two MCP tools:

### 1. `search_documents`

**Purpose:** Raw vector search for relevant chunks (debugging, custom workflows).

**Schema:**
```json
{
  "name": "search_documents",
  "description": "Search for relevant document chunks using vector similarity",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "top_k": {
        "type": "number",
        "description": "Number of results to return (default: 5)",
        "optional": true
      }
    },
    "required": ["query"]
  }
}
```

**Example:**
```
User: Find chunks about vacation policy
Assistant uses: search_documents(query="vacation policy", top_k=5)
Returns: [chunk1, chunk2, ...] with scores
```

---

### 2. `ask_question`

**Purpose:** Full RAG pipeline with grounded answer + citations.

**Schema:**
```json
{
  "name": "ask_question",
  "description": "Ask a question and get a grounded answer with citations from uploaded documents",
  "inputSchema": {
    "type": "object",
    "properties": {
      "question": {
        "type": "string",
        "description": "The question to answer"
      }
    },
    "required": ["question"]
  }
}
```

**Example:**
```
User: What is the refund policy?
Assistant uses: ask_question(question="What is the refund policy?")
Returns: {"answer": "...", "sources": [...]}
```

---

## Setup with Claude Desktop

### 1. Start MCP Server

```bash
# In your askdocs-rag-agent directory
docker compose up

# Or run MCP server directly
docker compose exec api python -m app.mcp.server
```

The MCP server runs alongside the REST API (shares database).

### 2. Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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
      "cwd": "/path/to/askdocs-rag-agent"
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
        "GEMINI_API_KEY": "your_key"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

Tools will appear in Claude Desktop's tool menu.

### 4. Test It

**In Claude Desktop:**
```
You: What is the vacation policy in my handbook?

Claude: I'll search your documents using the askdocs tool.
[Uses ask_question(question="What is the vacation policy?")]

Claude: According to your handbook.pdf (page 7), employees receive 15 days of paid vacation per year...
```

---

## Setup with Other MCP Clients

### Generic MCP Client

Any MCP-compatible client can connect via stdio:

```bash
# Start MCP server
python -m app.mcp.server

# MCP client connects via stdin/stdout
# Tools: search_documents, ask_question
```

### Custom Integration

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to MCP server
server_params = StdioServerParameters(
    command="python",
    args=["-m", "app.mcp.server"],
    env={"DATABASE_URL": "..."}
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # List tools
        tools = await session.list_tools()
        print(tools)

        # Call tool
        result = await session.call_tool(
            "ask_question",
            arguments={"question": "What is the refund policy?"}
        )
        print(result.content[0].text)
```

---

## MCP Server Implementation

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
            "description": "Search for relevant document chunks",
            "inputSchema": {...}
        },
        {
            "name": "ask_question",
            "description": "Ask a question and get grounded answer",
            "inputSchema": {...}
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

## Use Cases

### 1. Document Q&A in Claude Desktop

Upload PDFs via REST API → Ask questions in Claude Desktop using MCP tools.

**Workflow:**
```bash
# Upload document
curl -X POST http://localhost:8000/documents -F "file=@handbook.pdf"

# Ask via Claude Desktop
"What are the benefits described in my handbook?"
→ Claude uses ask_question tool → returns cited answer
```

---

### 2. Research Workflow

Search documents for evidence, then synthesize with Claude's reasoning.

**Example:**
```
You: Find all mentions of "remote work policy"

Claude: I'll search your documents.
[Uses search_documents(query="remote work policy", top_k=10)]

Claude: I found 10 relevant chunks across 3 documents:
- handbook.pdf (pages 12, 15, 18)
- covid-policy.pdf (pages 2, 5)
- 2025-updates.pdf (page 7)

Shall I summarize the key points?
```

---

### 3. Custom AI Workflows

Build agents that combine askdocs tools with other MCP tools.

**Example:**
```
Agent workflow:
1. Use ask_question to get company policy
2. Use web_search tool to check legal compliance
3. Use email tool to draft response to employee

All orchestrated via MCP.
```

---

## Troubleshooting

### Issue: Claude Desktop doesn't show tools

**Fix:**
1. Check `claude_desktop_config.json` syntax (valid JSON)
2. Verify `cwd` path is correct
3. Restart Claude Desktop completely
4. Check logs: `~/Library/Logs/Claude/mcp-server-askdocs.log`

---

### Issue: Tools error "Database connection failed"

**Fix:**
Ensure `DATABASE_URL` is set in MCP server env vars:

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

### Issue: Slow response times

**Cause:** Cold start (embedding model loading).

**Fix:**
Keep MCP server running in background:
```bash
# Start in background
python -m app.mcp.server &

# Keep process alive
```

---

## Security Considerations

**MCP tools run with full database access.**

**For production:**
- Add authentication (API keys)
- Scope tools to specific tenants
- Log all MCP tool calls for audit

**Example:**
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict, context: dict):
    # Verify API key
    api_key = context.get("api_key")
    if not verify_api_key(api_key):
        raise PermissionError("Invalid API key")

    # Scope to tenant
    tenant_id = get_tenant_from_key(api_key)
    return ask_question(arguments["question"], tenant_id=tenant_id)
```

---

## Future Enhancements

- [ ] `upload_document` tool (ingest via MCP)
- [ ] `list_documents` tool (see available docs)
- [ ] `delete_document` tool (remove docs)
- [ ] Streaming responses for long answers

---

## Next Steps

- **Configure:** Add MCP server to Claude Desktop
- **Test:** Upload docs via API, query via MCP tools
- **Extend:** Build custom workflows combining askdocs with other MCP tools

---

**Questions?** Open an issue on [GitHub](https://github.com/dinkar1708/askdocs-rag-agent/issues).
