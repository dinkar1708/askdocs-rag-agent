# Slack Integration

Ask questions about your documents directly from Slack using the AskDocs bot.

## Overview

The Slack integration allows teams to query your document knowledge base without leaving Slack. The bot provides grounded, cited answers with automatic source attribution.

## Features

- **Multiple Interaction Methods:**
  - Direct mentions: `@askdocs What is the vacation policy?`
  - Direct messages: Send DMs to the bot
  - Slash commands: `/askdocs help`, `/askdocs docs`, `/askdocs <question>`

- **Smart Routing:**
  - Automatically detects answerable vs off-topic questions
  - Returns "not found" when information isn't in documents
  - Asks for clarification on ambiguous queries

- **Source Citations:**
  - Automatic citations with filename and page numbers
  - Similarity scores showing match confidence
  - Limited to top 3 most relevant sources for readability

- **Threaded Responses:**
  - Responds in threads when mentioned in channels
  - Keeps conversations organized

## Setup

### 1. Create a Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it "AskDocs" and select your workspace
4. Navigate to "OAuth & Permissions"
5. Add these Bot Token Scopes:
   - `app_mentions:read` - Read messages that mention @askdocs
   - `chat:write` - Send messages
   - `commands` - Use slash commands
   - `im:history` - Read direct messages
   - `im:read` - View direct message info
   - `im:write` - Send direct messages

6. Install the app to your workspace
7. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 2. Configure Event Subscriptions

1. Navigate to "Event Subscriptions" in your app settings
2. Enable Events
3. Set Request URL to: `https://your-domain.com/slack/events`
4. Subscribe to bot events:
   - `app_mention` - When someone mentions @askdocs
   - `message.im` - Direct messages to the bot

5. Save changes

### 3. Create Slash Command

1. Navigate to "Slash Commands"
2. Create a new command:
   - Command: `/askdocs`
   - Request URL: `https://your-domain.com/slack/commands`
   - Short Description: "Ask questions about your documents"
   - Usage Hint: `[question or 'help' or 'docs']`

3. Save the command

### 4. Get Signing Secret

1. Navigate to "Basic Information"
2. Scroll to "App Credentials"
3. Copy the "Signing Secret"

### 5. Configure Environment Variables

Add these to your `.env` file:

```bash
# Slack Integration
SLACK_ENABLED=True
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
```

### 6. Deploy and Test

1. Restart your application to load the new configuration
2. Verify the bot is active:
   ```bash
   curl http://your-domain.com/slack/status
   ```
   Should return:
   ```json
   {
     "enabled": true,
     "status": "active"
   }
   ```

3. Test in Slack:
   - Invite the bot to a channel: `/invite @askdocs`
   - Mention it: `@askdocs What is the vacation policy?`
   - Or DM it directly

## Usage Examples

### Getting Help

```
/askdocs help
```

Returns:
```
*AskDocs Bot Commands*

• Ask a question: `@askdocs What is the vacation policy?`
• Direct message: Send a DM to AskDocs
• Get help: `/askdocs help`
• List documents: `/askdocs docs`

*Features:*
✓ Grounded answers from your documents
✓ Automatic citations with page numbers
✓ Returns "not found" when answer isn't in docs
```

### Listing Documents

```
/askdocs docs
```

Returns:
```
*Uploaded Documents (3):*

• employee_handbook.pdf (45 pages, 234 chunks)
• benefits_guide.pdf (12 pages, 78 chunks)
• it_policy.pdf (8 pages, 42 chunks)
```

### Asking Questions

**In a channel (mention required):**
```
@askdocs How many vacation days do employees get?
```

**Direct message:**
```
What is the remote work policy?
```

**Via slash command:**
```
/askdocs What are the health insurance options?
```

**Response example:**
```
*Answer:*
Full-time employees accrue 15 days of paid vacation per year, starting from their first day of employment. Vacation days can be carried over up to 5 days per year.

*Sources:*
1. employee_handbook.pdf, page 12 (92.5% match)
2. benefits_summary.pdf, page 3 (87.3% match)
3. pto_policy.pdf, page 1 (81.2% match)
```

## Architecture

### Components

1. **Slack API Router** (`app/api/slack.py`)
   - Handles webhook events from Slack
   - Endpoints: `/slack/events`, `/slack/commands`, `/slack/status`

2. **Slack Bot Service** (`app/services/slack_bot.py`)
   - Core bot logic using `slack-bolt` framework
   - Event handlers for mentions, DMs, and commands
   - RAG integration for question answering

3. **Integration Points:**
   - Uses the same RAG pipeline as the REST API
   - Reranking support (if enabled)
   - Query routing for intent detection
   - LLM provider abstraction

### Message Flow

```
Slack User Message
    ↓
Slack Platform
    ↓
POST /slack/events (webhook)
    ↓
SlackBotService.handle_question()
    ↓
retrieve_with_reranking() → Get relevant chunks
    ↓
get_query_router() → Determine intent (answer/clarify/refuse)
    ↓
get_llm_provider().generate_answer() → Generate response
    ↓
format_response() → Add citations
    ↓
say() → Send back to Slack
```

## Configuration Options

All configuration is done via environment variables in `.env`:

```bash
# Enable/disable the integration
SLACK_ENABLED=True  # or False

# Authentication
SLACK_BOT_TOKEN=xoxb-xxxxx
SLACK_SIGNING_SECRET=xxxxx

# RAG Settings (shared with REST API)
RERANKING_ENABLED=True
RETRIEVAL_INITIAL_K=30
RETRIEVAL_FINAL_K=5

# LLM Provider
LLM_PROVIDER=gemini  # or ollama, azure, mock
GEMINI_API_KEY=your_key_here
```

## Testing

The Slack integration includes comprehensive test coverage:

```bash
# Run Slack-specific tests
pytest app/tests/test_slack.py -v

# Test categories:
# - Bot initialization and configuration
# - Event handler registration
# - API endpoint behavior (enabled/disabled states)
# - Question handling with RAG integration
# - Command handling (/askdocs help, docs, questions)
# - Empty question handling
# - Error handling
```

**Test Results:** 17/17 tests passing ✓

## Security Considerations

1. **Request Verification:**
   - All Slack requests are verified using the signing secret
   - Protects against replay attacks and unauthorized access

2. **Environment Variables:**
   - Tokens and secrets stored in `.env` (never committed)
   - Use `.env.example` as a template

3. **Rate Limiting:**
   - Consider adding rate limiting for production use
   - Prevent abuse from automated scripts

4. **Permissions:**
   - Grant minimal required scopes
   - Review bot permissions regularly

## Troubleshooting

### Bot Not Responding

1. Check bot status:
   ```bash
   curl http://your-domain.com/slack/status
   ```

2. Verify environment variables are set:
   ```bash
   echo $SLACK_ENABLED
   echo $SLACK_BOT_TOKEN
   echo $SLACK_SIGNING_SECRET
   ```

3. Check application logs for errors:
   ```bash
   # Look for initialization errors
   grep "Slack bot" logs/app.log
   ```

### "Slack integration is not enabled" Error

- Ensure `SLACK_ENABLED=True` in `.env`
- Restart the application after changing environment variables
- Verify both `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` are set

### Event Verification Fails

- Double-check the signing secret matches Slack app settings
- Ensure request URL uses HTTPS (required by Slack)
- Check for clock skew between server and Slack

### No Response to Questions

1. Verify RAG system is working:
   ```bash
   # Test via REST API
   curl -X POST http://your-domain.com/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "test question"}'
   ```

2. Check documents are uploaded:
   ```bash
   curl http://your-domain.com/documents
   ```

3. Review LLM provider configuration:
   - Verify API keys are valid
   - Check LLM provider is accessible

## Performance Optimization

### Response Time

- Enable reranking for better answer quality (slight latency increase)
- Use a faster LLM provider for production
- Consider caching frequently asked questions

### Concurrent Users

- The bot handles concurrent requests automatically
- FastAPI provides async request handling
- Database connection pooling is configured

### Cost Optimization

- Use `LLM_PROVIDER=ollama` for local, free inference
- Adjust `RETRIEVAL_FINAL_K` to reduce LLM context size
- Implement question deduplication to reduce API calls

## Testing with Free Slack Workspace

You can test the Slack integration using a free Slack workspace and ngrok.

### Quick Test Setup (Local)

**1. Install ngrok:**
```bash
brew install ngrok
ngrok http 8000
# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

**2. Create Slack App:**
- Go to https://api.slack.com/apps → Create New App
- Add bot scopes: `app_mentions:read`, `chat:write`, `commands`, `im:history`, `im:read`, `im:write`
- Install to workspace → Copy Bot Token and Signing Secret

**3. Configure Event Subscriptions:**
- Enable Events → URL: `https://abc123.ngrok.io/slack/events`
- Subscribe to: `app_mention`, `message.im`

**4. Create Slash Command:**
- Command: `/askdocs`
- URL: `https://abc123.ngrok.io/slack/commands`

**5. Update .env and Restart:**
```bash
SLACK_ENABLED=True
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret

docker compose restart api
```

**6. Test in Slack:**
```
# Upload a document first
curl -X POST https://abc123.ngrok.io/documents/ \
  -F "file=@app/samples/company_policy.pdf"

# In Slack:
/invite @askdocs
@askdocs What is the vacation policy?
```

### Test Cases

**✓ @Mentions:**
```
@askdocs What is the vacation policy?
```

**✓ Direct Messages:**
```
How many sick days do employees get?
```

**✓ Slash Commands:**
```
/askdocs help
/askdocs docs
/askdocs What are the office hours?
```

**✓ Error Cases:**
```
@askdocs What's the weather?  # Should refuse (off-topic)
/askdocs                       # Should show help
```

### Testing Tips

- **Free Tier:** Slack workspace (free) + ngrok (free) + Ollama (free local LLM)
- **ngrok URL Changes:** Free tier URL changes on restart - update Slack URLs each time
- **Check Status:** `curl https://abc123.ngrok.io/slack/status`
- **View Logs:** `docker compose logs api | grep Slack`

For detailed troubleshooting, see the **Troubleshooting** section above.

## Roadmap

Potential future enhancements:

- [ ] Conversation memory (multi-turn dialogues)
- [ ] Interactive buttons for feedback (helpful/not helpful)
- [ ] Document upload via Slack file sharing
- [ ] User-specific document access controls
- [ ] Analytics dashboard for question patterns
- [ ] Scheduled summaries of frequently asked questions
- [ ] Multi-language support

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/askdocs-rag-agent/issues
- Documentation: See main README.md
- Test Examples: `app/tests/test_slack.py`
- Testing Guide: See "Testing with Free Slack Workspace" section above

## License

Same as the main project license.
