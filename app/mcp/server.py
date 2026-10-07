"""AskDocs Model Context Protocol (MCP) Server

Exposes AskDocs RAG tools (search_documents, ask_question, list_documents, summarize_document)
over standard JSON-RPC 2.0 stdio protocol to Claude Desktop, Gemini CLI, Cursor, and other MCP clients.
"""

import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.llm.factory import get_llm_provider
from app.llm.base import BaseLLMProvider
from app.mcp.tools import (
    tool_search_documents,
    tool_ask_question,
    tool_list_documents,
    tool_summarize_document
)

# Direct all application logs to stderr so stdout remains clean for MCP JSON-RPC
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[askdocs-mcp] %(levelname)s: %(message)s"
)
logger = logging.getLogger("askdocs-mcp")

# MCP Tool Definitions Schema
MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "search_documents",
        "description": "Vector search for relevant document chunks using semantic similarity",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "ask_question",
        "description": "Ask a question and get a grounded answer with citations from uploaded documents",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to answer"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of sources to retrieve (default: 5)",
                    "default": 5
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "list_documents",
        "description": "List all uploaded documents in the AskDocs knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of documents to return (default: 20)",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "summarize_document",
        "description": "Generate an executive or detailed summary for an uploaded document",
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "integer",
                    "description": "ID of document to summarize"
                },
                "summary_type": {
                    "type": "string",
                    "description": "Type of summary: executive, detailed, key_points",
                    "default": "executive"
                }
            },
            "required": ["document_id"]
        }
    }
]


class AskDocsMCPServer:
    """Model Context Protocol stdio server for AskDocs"""

    def __init__(self, db_session_factory=SessionLocal, llm_provider: Optional[BaseLLMProvider] = None):
        self.db_session_factory = db_session_factory
        self.llm_provider = llm_provider

    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process incoming JSON-RPC 2.0 message and construct response.

        Args:
            request: Parsed JSON-RPC dictionary

        Returns:
            JSON-RPC response dictionary, or None if message is a notification
        """
        msg_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        # Handle notifications (no response required)
        if method == "notifications/initialized" or method == "initialized":
            logger.info("Client completed initialization handshake")
            return None

        # 1. Initialize
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "askdocs",
                        "version": "0.1.0"
                    }
                }
            }

        # 2. Ping
        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {}
            }

        # 3. Tools List
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": MCP_TOOLS
                }
            }

        # 4. Tools Call
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            logger.info(f"Executing tool call: {tool_name} with arguments: {arguments}")

            tool_result = await self.execute_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": tool_result
            }

        # Method Not Found
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                }
            }

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool and format MCP result structure"""
        db = self.db_session_factory()
        try:
            if name == "search_documents":
                query = arguments.get("query", "")
                top_k = int(arguments.get("top_k", 5))
                res = tool_search_documents(db=db, query=query, top_k=top_k)
                text_content = json.dumps(res, indent=2)

            elif name == "ask_question":
                question = arguments.get("question", "")
                top_k = int(arguments.get("top_k", 5))
                res = await tool_ask_question(
                    db=db,
                    question=question,
                    top_k=top_k,
                    llm_provider=self.llm_provider
                )
                text_content = json.dumps(res, indent=2)

            elif name == "list_documents":
                limit = int(arguments.get("limit", 20))
                res = tool_list_documents(db=db, limit=limit)
                text_content = json.dumps(res, indent=2)

            elif name == "summarize_document":
                doc_id = int(arguments.get("document_id"))
                summary_type = arguments.get("summary_type", "executive")
                res = await tool_summarize_document(
                    db=db,
                    document_id=doc_id,
                    summary_type=summary_type,
                    llm_provider=self.llm_provider
                )
                text_content = json.dumps(res, indent=2)

            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: Unknown tool '{name}'"
                        }
                    ],
                    "isError": True
                }

            return {
                "content": [
                    {
                        "type": "text",
                        "text": text_content
                    }
                ],
                "isError": False
            }

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}", exc_info=True)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing tool {name}: {str(e)}"
                    }
                ],
                "isError": True
            }
        finally:
            db.close()

    async def run_stdio(self):
        """Standard input/output event loop for MCP JSON-RPC messages"""
        logger.info("AskDocs MCP server started listening on stdio")
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_running_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line_bytes = await reader.readline()
            if not line_bytes:
                break

            line = line_bytes.decode("utf-8").strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
                continue

            response = await self.handle_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()


def create_mcp_server(db_session_factory=SessionLocal, llm_provider: Optional[BaseLLMProvider] = None) -> AskDocsMCPServer:
    """Factory function for AskDocsMCPServer"""
    return AskDocsMCPServer(db_session_factory=db_session_factory, llm_provider=llm_provider)


async def main():
    server = create_mcp_server()
    await server.run_stdio()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("AskDocs MCP server stopped")
