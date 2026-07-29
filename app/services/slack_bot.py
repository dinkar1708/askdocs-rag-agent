"""Slack Bot Service

Handles Slack events and messages for the AskDocs bot.
"""

import logging
from typing import Dict, Any, Optional
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk import WebClient

from app.services.retriever import retrieve_relevant_chunks, retrieve_with_reranking, format_context_for_llm
from app.db.database import get_db
from app.core.config import settings
from app.llm.factory import get_llm_provider
from app.graph.router import get_query_router

logger = logging.getLogger(__name__)


class SlackBotService:
    """Service for handling Slack bot interactions"""

    def __init__(self, bot_token: str, signing_secret: str):
        """Initialize Slack bot

        Args:
            bot_token: Slack bot token (xoxb-...)
            signing_secret: Slack signing secret for request verification
        """
        self.app = App(
            token=bot_token,
            signing_secret=signing_secret,
        )
        self.client = WebClient(token=bot_token)
        self.handler = SlackRequestHandler(self.app)

        # Register event handlers
        self._register_handlers()

        logger.info("Slack bot initialized successfully")

    def _register_handlers(self):
        """Register all Slack event handlers"""

        # Handle @mentions in channels
        @self.app.event("app_mention")
        def handle_mention(event, say, logger):
            """Handle when bot is mentioned in a channel"""
            logger.info(f"Received mention: {event}")
            self._handle_question(event, say)

        # Handle direct messages
        @self.app.event("message")
        def handle_message(event, say, logger):
            """Handle direct messages to the bot"""
            # Ignore bot messages and threaded messages
            if event.get("subtype") or event.get("bot_id") or event.get("thread_ts"):
                return

            logger.info(f"Received DM: {event}")
            self._handle_question(event, say)

        # Handle /askdocs slash command
        @self.app.command("/askdocs")
        def handle_command(ack, command, respond):
            """Handle /askdocs slash command"""
            ack()  # Acknowledge command immediately
            logger.info(f"Received command: {command}")
            self._handle_command(command, respond)

    def _handle_question(self, event: Dict[str, Any], say):
        """Handle question from user

        Args:
            event: Slack event data
            say: Function to send message back to Slack
        """
        try:
            # Extract question text
            text = event.get("text", "")

            # Remove bot mention if present
            text = text.replace(f"<@{event.get('user')}>", "").strip()

            if not text:
                say("Please ask a question about your documents!")
                return

            # Show typing indicator
            channel = event.get("channel")
            thread_ts = event.get("ts")  # For threading responses

            # Query the RAG system
            db = next(get_db())
            try:
                # Retrieve relevant chunks
                if settings.RERANKING_ENABLED:
                    chunks = retrieve_with_reranking(
                        query=text,
                        db=db,
                        initial_k=settings.RETRIEVAL_INITIAL_K,
                        final_k=5
                    )
                else:
                    chunks = retrieve_relevant_chunks(
                        query=text,
                        db=db,
                        top_k=5
                    )

                # Route the query
                router = get_query_router()
                route_result = router.route(question=text, chunks=chunks)
                intent = route_result["intent"]

                # Generate response based on intent
                answer = ""
                sources = []

                if intent == "answer":
                    # Format context and generate answer
                    context = format_context_for_llm(chunks)
                    llm = get_llm_provider()
                    answer = llm.generate_answer(question=text, context=context)
                    sources = chunks
                elif intent == "clarify":
                    answer = route_result.get("clarification", "Could you please rephrase your question? I need more context to help you.")
                else:  # refuse
                    answer = route_result.get("refusal", "I cannot find relevant information in the uploaded documents to answer this question.")

                # Build response message
                response_text = f"*Answer:*\n{answer}"

                if sources:
                    response_text += "\n\n*Sources:*"
                    for idx, source in enumerate(sources[:3], 1):  # Limit to 3 sources
                        filename = source.get("filename", "Unknown")
                        page = source.get("page_number", "?")
                        score = source.get("similarity_score", 0)
                        response_text += f"\n{idx}. {filename}, page {page} ({score*100:.1f}% match)"

                # Send response (in thread if in channel)
                say(
                    text=response_text,
                    thread_ts=thread_ts if channel else None
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling question: {e}", exc_info=True)
            say(f"Sorry, I encountered an error: {str(e)}")

    def _handle_command(self, command: Dict[str, Any], respond):
        """Handle /askdocs slash command

        Args:
            command: Slack command data
            respond: Function to send response
        """
        try:
            # Get command text
            text = command.get("text", "").strip().lower()

            if text == "help" or text == "":
                # Show help message
                help_text = """
*AskDocs Bot Commands*

• Ask a question: `@askdocs What is the vacation policy?`
• Direct message: Send a DM to AskDocs
• Get help: `/askdocs help`
• List documents: `/askdocs docs`

*Features:*
✓ Grounded answers from your documents
✓ Automatic citations with page numbers
✓ Returns "not found" when answer isn't in docs
"""
                respond(help_text)

            elif text == "docs" or text == "documents":
                # List uploaded documents
                db = next(get_db())
                try:
                    from app.db.models import Document
                    documents = db.query(Document).all()

                    if not documents:
                        respond("No documents uploaded yet. Upload PDFs via the API or web interface.")
                        return

                    docs_text = f"*Uploaded Documents ({len(documents)}):*\n\n"
                    for doc in documents[:10]:  # Limit to 10
                        docs_text += f"• {doc.filename} ({doc.page_count} pages, {len(doc.chunks)} chunks)\n"

                    if len(documents) > 10:
                        docs_text += f"\n_...and {len(documents) - 10} more documents_"

                    respond(docs_text)
                finally:
                    db.close()

            else:
                # Treat as a question
                db = next(get_db())
                try:
                    # Retrieve relevant chunks
                    if settings.RERANKING_ENABLED:
                        chunks = retrieve_with_reranking(
                            query=text,
                            db=db,
                            initial_k=settings.RETRIEVAL_INITIAL_K,
                            final_k=5
                        )
                    else:
                        chunks = retrieve_relevant_chunks(
                            query=text,
                            db=db,
                            top_k=5
                        )

                    # Route the query
                    router = get_query_router()
                    route_result = router.route(question=text, chunks=chunks)
                    intent = route_result["intent"]

                    # Generate response based on intent
                    answer = ""
                    sources = []

                    if intent == "answer":
                        # Format context and generate answer
                        context = format_context_for_llm(chunks)
                        llm = get_llm_provider()
                        answer = llm.generate_answer(question=text, context=context)
                        sources = chunks
                    elif intent == "clarify":
                        answer = route_result.get("clarification", "Could you please rephrase your question?")
                    else:  # refuse
                        answer = route_result.get("refusal", "I cannot find relevant information in the documents.")

                    response_text = f"*Answer:*\n{answer}"

                    if sources:
                        response_text += "\n\n*Sources:*"
                        for idx, source in enumerate(sources[:3], 1):
                            filename = source.get("filename", "Unknown")
                            page = source.get("page_number", "?")
                            response_text += f"\n{idx}. {filename}, page {page}"

                    respond(response_text)
                finally:
                    db.close()

        except Exception as e:
            logger.error(f"Error handling command: {e}", exc_info=True)
            respond(f"Sorry, I encountered an error: {str(e)}")

    def get_handler(self):
        """Get the FastAPI request handler

        Returns:
            SlackRequestHandler for use with FastAPI
        """
        return self.handler


# Global bot instance (initialized when Slack is enabled)
_slack_bot: Optional[SlackBotService] = None


def get_slack_bot() -> Optional[SlackBotService]:
    """Get the global Slack bot instance

    Returns:
        SlackBotService instance or None if Slack is not enabled
    """
    global _slack_bot

    if _slack_bot is None:
        # Initialize bot if Slack is enabled and credentials are available
        if (hasattr(settings, 'SLACK_ENABLED') and settings.SLACK_ENABLED and
            hasattr(settings, 'SLACK_BOT_TOKEN') and settings.SLACK_BOT_TOKEN and
            hasattr(settings, 'SLACK_SIGNING_SECRET') and settings.SLACK_SIGNING_SECRET):

            try:
                _slack_bot = SlackBotService(
                    bot_token=settings.SLACK_BOT_TOKEN,
                    signing_secret=settings.SLACK_SIGNING_SECRET
                )
                logger.info("Slack bot service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Slack bot: {e}")
                return None

    return _slack_bot


def is_slack_enabled() -> bool:
    """Check if Slack integration is enabled

    Returns:
        True if Slack is enabled and configured
    """
    return get_slack_bot() is not None
