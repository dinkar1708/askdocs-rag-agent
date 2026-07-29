"""Tests for Slack integration

Tests the Slack bot service and API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.slack_bot import SlackBotService, get_slack_bot, is_slack_enabled


@pytest.fixture
def mock_slack_settings():
    """Mock Slack settings"""
    with patch("app.services.slack_bot.settings") as mock_settings:
        mock_settings.SLACK_ENABLED = True
        mock_settings.SLACK_BOT_TOKEN = "xoxb-test-token"
        mock_settings.SLACK_SIGNING_SECRET = "test-signing-secret"
        yield mock_settings


@pytest.fixture
def mock_slack_app():
    """Mock Slack Bolt App"""
    with patch("app.services.slack_bot.App") as mock_app_class:
        mock_app_instance = MagicMock()
        mock_app_class.return_value = mock_app_instance
        yield mock_app_instance


@pytest.fixture
def mock_web_client():
    """Mock Slack WebClient"""
    with patch("app.services.slack_bot.WebClient") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        yield mock_client_instance


@pytest.fixture
def mock_handler():
    """Mock SlackRequestHandler"""
    with patch("app.services.slack_bot.SlackRequestHandler") as mock_handler_class:
        mock_handler_instance = MagicMock()
        mock_handler_class.return_value = mock_handler_instance
        yield mock_handler_instance


class TestSlackBotService:
    """Test SlackBotService class"""

    def test_slack_bot_initialization(self, mock_slack_app, mock_web_client, mock_handler):
        """Test that Slack bot initializes correctly"""
        bot = SlackBotService(
            bot_token="xoxb-test-token",
            signing_secret="test-signing-secret"
        )

        assert bot.app is not None
        assert bot.client is not None
        assert bot.handler is not None

    def test_slack_bot_registers_handlers(self, mock_slack_app, mock_web_client, mock_handler):
        """Test that event handlers are registered"""
        bot = SlackBotService(
            bot_token="xoxb-test-token",
            signing_secret="test-signing-secret"
        )

        # Verify event and command handlers were registered
        assert mock_slack_app.event.called
        assert mock_slack_app.command.called

    def test_get_handler(self, mock_slack_app, mock_web_client, mock_handler):
        """Test getting the request handler"""
        bot = SlackBotService(
            bot_token="xoxb-test-token",
            signing_secret="test-signing-secret"
        )

        handler = bot.get_handler()
        assert handler is not None


class TestSlackBotHelpers:
    """Test helper functions"""

    def test_is_slack_enabled_when_disabled(self):
        """Test is_slack_enabled returns False when disabled"""
        with patch("app.services.slack_bot.settings") as mock_settings:
            mock_settings.SLACK_ENABLED = False

            # Reset global bot instance
            import app.services.slack_bot
            app.services.slack_bot._slack_bot = None

            assert is_slack_enabled() is False

    def test_is_slack_enabled_when_enabled(self, mock_slack_settings, mock_slack_app, mock_web_client, mock_handler):
        """Test is_slack_enabled returns True when enabled"""
        # Reset global bot instance
        import app.services.slack_bot
        app.services.slack_bot._slack_bot = None

        enabled = is_slack_enabled()
        assert enabled is True

    def test_get_slack_bot_returns_singleton(self, mock_slack_settings, mock_slack_app, mock_web_client, mock_handler):
        """Test that get_slack_bot returns the same instance"""
        # Reset global bot instance
        import app.services.slack_bot
        app.services.slack_bot._slack_bot = None

        bot1 = get_slack_bot()
        bot2 = get_slack_bot()

        assert bot1 is bot2


class TestSlackAPIEndpoints:
    """Test Slack API endpoints"""

    def test_slack_status_disabled(self):
        """Test /slack/status when disabled"""
        with patch("app.api.slack.is_slack_enabled", return_value=False):
            client = TestClient(app)
            response = client.get("/slack/status")

            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is False
            assert data["status"] == "disabled"

    def test_slack_status_enabled(self):
        """Test /slack/status when enabled"""
        with patch("app.api.slack.is_slack_enabled", return_value=True):
            client = TestClient(app)
            response = client.get("/slack/status")

            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is True
            assert data["status"] == "active"

    def test_slack_events_disabled(self):
        """Test /slack/events returns 503 when disabled"""
        with patch("app.api.slack.is_slack_enabled", return_value=False):
            client = TestClient(app)
            response = client.post("/slack/events", json={})

            assert response.status_code == 503
            assert "not enabled" in response.json()["detail"]

    def test_slack_commands_disabled(self):
        """Test /slack/commands returns 503 when disabled"""
        with patch("app.api.slack.is_slack_enabled", return_value=False):
            client = TestClient(app)
            response = client.post("/slack/commands", json={})

            assert response.status_code == 503
            assert "not enabled" in response.json()["detail"]

    def test_slack_events_enabled(self):
        """Test /slack/events when enabled"""
        mock_bot = MagicMock()
        mock_handler = MagicMock()
        mock_handler.handle = MagicMock(return_value={"ok": True})
        mock_bot.get_handler.return_value = mock_handler

        with patch("app.api.slack.is_slack_enabled", return_value=True), \
             patch("app.api.slack.get_slack_bot", return_value=mock_bot):

            client = TestClient(app)
            response = client.post("/slack/events", json={"type": "url_verification", "challenge": "test"})

            # Handler should be called
            mock_handler.handle.assert_called_once()

    def test_slack_commands_enabled(self):
        """Test /slack/commands when enabled"""
        mock_bot = MagicMock()
        mock_handler = MagicMock()
        mock_handler.handle = MagicMock(return_value={"ok": True})
        mock_bot.get_handler.return_value = mock_handler

        with patch("app.api.slack.is_slack_enabled", return_value=True), \
             patch("app.api.slack.get_slack_bot", return_value=mock_bot):

            client = TestClient(app)
            response = client.post("/slack/commands", data={"command": "/askdocs", "text": "help"})

            # Handler should be called
            mock_handler.handle.assert_called_once()


class TestSlackQuestionHandling:
    """Test question handling logic"""

    def test_handle_question_with_rag_integration(self, mock_slack_app, mock_web_client, mock_handler):
        """Test that questions are handled with RAG integration"""
        with patch("app.services.slack_bot.retrieve_with_reranking") as mock_retrieve, \
             patch("app.services.slack_bot.get_query_router") as mock_router, \
             patch("app.services.slack_bot.get_llm_provider") as mock_llm, \
             patch("app.services.slack_bot.format_context_for_llm") as mock_format, \
             patch("app.services.slack_bot.get_db") as mock_get_db, \
             patch("app.services.slack_bot.settings") as mock_settings:

            # Mock settings
            mock_settings.RERANKING_ENABLED = True
            mock_settings.RETRIEVAL_INITIAL_K = 30

            # Mock chunks
            mock_chunks = [
                {
                    "filename": "test.pdf",
                    "page_number": 1,
                    "similarity_score": 0.95,
                    "text": "Test content"
                }
            ]
            mock_retrieve.return_value = mock_chunks

            # Mock router
            mock_router_instance = MagicMock()
            mock_router_instance.route.return_value = {
                "intent": "answer",
                "confidence": 0.9,
                "reason": "Found relevant content"
            }
            mock_router.return_value = mock_router_instance

            # Mock LLM
            mock_llm_instance = MagicMock()
            mock_llm_instance.generate_answer.return_value = "Test answer"
            mock_llm.return_value = mock_llm_instance

            # Mock format
            mock_format.return_value = "Formatted context"

            # Mock database
            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])

            bot = SlackBotService(
                bot_token="xoxb-test-token",
                signing_secret="test-signing-secret"
            )

            # Simulate question event
            mock_say = MagicMock()
            event = {
                "text": "What is the vacation policy?",
                "user": "U123",
                "channel": "C123",
                "ts": "1234567890.123"
            }

            bot._handle_question(event, mock_say)

            # Verify retrieval was called
            mock_retrieve.assert_called_once()

            # Verify response was sent
            mock_say.assert_called_once()
            call_args = mock_say.call_args
            assert "Test answer" in call_args.kwargs["text"]

    def test_handle_empty_question(self, mock_slack_app, mock_web_client, mock_handler):
        """Test handling of empty questions"""
        bot = SlackBotService(
            bot_token="xoxb-test-token",
            signing_secret="test-signing-secret"
        )

        mock_say = MagicMock()
        event = {
            "text": "",
            "user": "U123"
        }

        bot._handle_question(event, mock_say)

        # Should ask for a question
        mock_say.assert_called_once()
        call_args = mock_say.call_args
        assert "ask a question" in call_args[0][0].lower()


class TestSlackCommandHandling:
    """Test command handling logic"""

    def test_handle_help_command(self, mock_slack_app, mock_web_client, mock_handler):
        """Test /askdocs help command"""
        bot = SlackBotService(
            bot_token="xoxb-test-token",
            signing_secret="test-signing-secret"
        )

        mock_respond = MagicMock()
        command = {"text": "help"}

        bot._handle_command(command, mock_respond)

        # Should return help text
        mock_respond.assert_called_once()
        call_args = mock_respond.call_args
        assert "AskDocs Bot Commands" in call_args[0][0]

    def test_handle_docs_command(self, mock_slack_app, mock_web_client, mock_handler):
        """Test /askdocs docs command"""
        with patch("app.services.slack_bot.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_doc = MagicMock()
            mock_doc.filename = "test.pdf"
            mock_doc.page_count = 10
            mock_db.query.return_value.all.return_value = [mock_doc]
            mock_get_db.return_value = iter([mock_db])

            bot = SlackBotService(
                bot_token="xoxb-test-token",
                signing_secret="test-signing-secret"
            )

            mock_respond = MagicMock()
            command = {"text": "docs"}

            bot._handle_command(command, mock_respond)

            # Should return document list
            mock_respond.assert_called_once()
            call_args = mock_respond.call_args
            assert "test.pdf" in call_args[0][0]
            assert "10 pages" in call_args[0][0]

    def test_handle_question_via_command(self, mock_slack_app, mock_web_client, mock_handler):
        """Test asking a question via /askdocs command"""
        with patch("app.services.slack_bot.retrieve_with_reranking") as mock_retrieve, \
             patch("app.services.slack_bot.get_query_router") as mock_router, \
             patch("app.services.slack_bot.get_llm_provider") as mock_llm, \
             patch("app.services.slack_bot.format_context_for_llm") as mock_format, \
             patch("app.services.slack_bot.get_db") as mock_get_db, \
             patch("app.services.slack_bot.settings") as mock_settings:

            # Mock settings
            mock_settings.RERANKING_ENABLED = True
            mock_settings.RETRIEVAL_INITIAL_K = 30

            # Mock chunks
            mock_retrieve.return_value = []

            # Mock router
            mock_router_instance = MagicMock()
            mock_router_instance.route.return_value = {
                "intent": "answer",
                "confidence": 0.9,
                "reason": "Found answer"
            }
            mock_router.return_value = mock_router_instance

            # Mock LLM
            mock_llm_instance = MagicMock()
            mock_llm_instance.generate_answer.return_value = "42"
            mock_llm.return_value = mock_llm_instance

            # Mock format
            mock_format.return_value = "Context"

            mock_db = MagicMock()
            mock_get_db.return_value = iter([mock_db])

            bot = SlackBotService(
                bot_token="xoxb-test-token",
                signing_secret="test-signing-secret"
            )

            mock_respond = MagicMock()
            command = {"text": "What is the answer?"}

            bot._handle_command(command, mock_respond)

            # Should call retrieval and respond
            mock_retrieve.assert_called_once()
            mock_respond.assert_called_once()
            call_args = mock_respond.call_args
            assert "42" in call_args[0][0]
