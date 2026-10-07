"""Tests for MCP Integration (Feature 06)"""

import pytest
import json
from app.mcp.server import create_mcp_server, MCP_TOOLS
from app.llm.mock_provider import MockLLMProvider


@pytest.fixture
def mcp_server(db_session):
    """Create MCP server with test DB session and mock LLM provider"""
    def session_factory():
        return db_session

    return create_mcp_server(
        db_session_factory=session_factory,
        llm_provider=MockLLMProvider()
    )


@pytest.mark.asyncio
async def test_mcp_initialize(mcp_server):
    """Test MCP protocol initialization handshake"""
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    resp = await mcp_server.handle_request(req)
    assert resp is not None
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert "protocolVersion" in resp["result"]
    assert resp["result"]["serverInfo"]["name"] == "askdocs"


@pytest.mark.asyncio
async def test_mcp_ping(mcp_server):
    """Test MCP ping request"""
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "ping"
    }
    resp = await mcp_server.handle_request(req)
    assert resp is not None
    assert resp["id"] == 2
    assert resp["result"] == {}


@pytest.mark.asyncio
async def test_mcp_notification_initialized(mcp_server):
    """Test initialized notification returns None (no response)"""
    req = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    resp = await mcp_server.handle_request(req)
    assert resp is None


@pytest.mark.asyncio
async def test_mcp_tools_list(mcp_server):
    """Test listing available MCP tools"""
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/list"
    }
    resp = await mcp_server.handle_request(req)
    assert resp is not None
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "search_documents" in tool_names
    assert "ask_question" in tool_names
    assert "list_documents" in tool_names
    assert "summarize_document" in tool_names


@pytest.mark.asyncio
async def test_mcp_search_documents(mcp_server, sample_document_with_chunks):
    """Test executing search_documents tool via MCP"""
    doc, chunks = sample_document_with_chunks
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "search_documents",
            "arguments": {
                "query": "vacation policy",
                "top_k": 3
            }
        }
    }
    resp = await mcp_server.handle_request(req)
    assert resp is not None
    assert resp["result"]["isError"] is False
    content_text = resp["result"]["content"][0]["text"]
    data = json.loads(content_text)
    assert data["query"] == "vacation policy"
    assert len(data["chunks"]) > 0


@pytest.mark.asyncio
async def test_mcp_ask_question(mcp_server, sample_document_with_chunks):
    """Test executing ask_question tool via MCP"""
    doc, chunks = sample_document_with_chunks
    req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "ask_question",
            "arguments": {
                "question": "How many days of paid vacation do employees accrue?",
                "top_k": 3
            }
        }
    }
    resp = await mcp_server.handle_request(req)
    assert resp is not None
    assert resp["result"]["isError"] is False
    data = json.loads(resp["result"]["content"][0]["text"])
    assert "answer" in data
    assert len(data["sources"]) > 0


@pytest.mark.asyncio
async def test_mcp_list_documents(mcp_server, sample_document_with_chunks):
    """Test executing list_documents tool via MCP"""
    req = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "list_documents",
            "arguments": {"limit": 10}
        }
    }
    resp = await mcp_server.handle_request(req)
    assert resp is not None
    assert resp["result"]["isError"] is False
    data = json.loads(resp["result"]["content"][0]["text"])
    assert len(data) >= 1
    assert data[0]["filename"] == "company_policy.pdf"


@pytest.mark.asyncio
async def test_mcp_summarize_document(mcp_server, sample_document_with_chunks):
    """Test executing summarize_document tool via MCP"""
    doc, chunks = sample_document_with_chunks
    req = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "summarize_document",
            "arguments": {
                "document_id": doc.id,
                "summary_type": "executive"
            }
        }
    }
    resp = await mcp_server.handle_request(req)
    assert resp is not None
    assert resp["result"]["isError"] is False
    data = json.loads(resp["result"]["content"][0]["text"])
    assert data["document_id"] == doc.id
    assert len(data["summary"]) > 0


@pytest.mark.asyncio
async def test_mcp_unknown_method(mcp_server):
    """Test error on unknown JSON-RPC method"""
    req = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "nonexistent/method",
        "params": {}
    }
    resp = await mcp_server.handle_request(req)
    assert resp is not None
    assert "error" in resp
    assert resp["error"]["code"] == -32601


@pytest.mark.asyncio
async def test_mcp_unknown_tool(mcp_server):
    """Test error when calling an unknown tool name"""
    req = {
        "jsonrpc": "2.0",
        "id": 9,
        "method": "tools/call",
        "params": {
            "name": "unknown_tool",
            "arguments": {}
        }
    }
    resp = await mcp_server.handle_request(req)
    assert resp is not None
    assert resp["result"]["isError"] is True
    assert "Unknown tool" in resp["result"]["content"][0]["text"]
