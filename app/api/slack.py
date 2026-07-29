"""Slack API endpoints

Handles Slack webhook events and slash commands.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response

from app.services.slack_bot import get_slack_bot, is_slack_enabled

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/slack", tags=["slack"])


@router.post("/events")
async def slack_events(request: Request):
    """Handle Slack events webhook

    This endpoint receives all Slack events (mentions, DMs, etc.)
    """
    if not is_slack_enabled():
        raise HTTPException(status_code=503, detail="Slack integration is not enabled")

    slack_bot = get_slack_bot()
    if not slack_bot:
        raise HTTPException(status_code=503, detail="Slack bot not initialized")

    try:
        # Use Slack Bolt's request handler to process the event
        handler = slack_bot.get_handler()
        return await handler.handle(request)
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commands")
async def slack_commands(request: Request):
    """Handle Slack slash commands

    This endpoint receives slash commands like /askdocs
    """
    if not is_slack_enabled():
        raise HTTPException(status_code=503, detail="Slack integration is not enabled")

    slack_bot = get_slack_bot()
    if not slack_bot:
        raise HTTPException(status_code=503, detail="Slack bot not initialized")

    try:
        # Use Slack Bolt's request handler to process the command
        handler = slack_bot.get_handler()
        return await handler.handle(request)
    except Exception as e:
        logger.error(f"Error handling Slack command: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def slack_status():
    """Get Slack integration status"""
    enabled = is_slack_enabled()
    return {
        "enabled": enabled,
        "status": "active" if enabled else "disabled"
    }
