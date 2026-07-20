# Slack Bot Integration

Ask questions from Slack.

---

## Overview

Slack bot that answers questions from your documents.

**Features:**
- Ask questions in any channel
- DM the bot privately
- Upload documents via Slack
- Get answers with citations

---

## Setup

### 1. Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Name: "AskDocs Bot"
5. Select workspace

### 2. Configure Bot

**Add scopes:**
- `chat:write` - Send messages
- `files:read` - Read uploaded files
- `commands` - Slash commands

**Enable events:**
- `app_mention` - @askdocs questions
- `message.im` - DM questions

### 3. Get Credentials

Copy from Slack app settings:
- Bot Token: `xoxb-...`
- Signing Secret: `abc123...`

### 4. Configure AskDocs

See [core/configuration/](../../core/configuration/)

```bash
# .env
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret
SLACK_ENABLED=true
```

### 5. Deploy

See [core/deployment/](../../core/deployment/)

```bash
# Start with Slack enabled
docker compose up -d
```

### 6. Install to Workspace

1. Go to Slack app settings
2. Click "Install to Workspace"
3. Authorize permissions

---

## Usage

### Ask in Channel

```
@askdocs What is the vacation policy?
```

Bot responds:
```
15 days paid vacation per year.
Source: handbook.pdf, page 7
```

### Ask via DM

Direct message the bot:
```
What is the refund policy?
```

### Slash Commands

```
/askdocs help
/askdocs docs
/askdocs upload [attach PDF]
```

---

## Examples

### HR Channel

```
#hr-questions

User: @askdocs How many sick days do I get?
Bot: Full-time employees receive 10 sick days per year.
     Source: handbook.pdf, page 8
```

### Support Channel

```
#customer-support

User: @askdocs What's the shipping time?
Bot: Standard shipping takes 3-5 business days.
     Source: shipping-policy.pdf, page 2
```

---

## Commands

**Help:**
```
/askdocs help
```

**List documents:**
```
/askdocs docs
```

**Upload document:**
```
/askdocs upload
[Attach PDF file]
```

---

## Security

See [core/security/](../../core/security/)

**Permissions:**
- Only workspace members can ask
- Admins can upload documents
- DMs are private

**Token security:**
- Store tokens in env vars
- Rotate tokens every 90 days

---

## Troubleshooting

**Bot not responding:**
- Check bot is online: `/askdocs help`
- Verify token in config
- Check event subscriptions URL

**Wrong answers:**
- Upload correct documents
- Check document processed: `/askdocs docs`

**Rate limits:**
- Slack: 1 message/sec
- AskDocs: See [core/security/API_SECURITY.md](../../core/security/API_SECURITY.md)

---

## Advanced

### Custom Responses

```python
# Custom bot behavior
if question.startswith("urgent:"):
    # Priority handling
    response = ask_with_priority(question)
```

### Analytics

Track usage:
- Questions per channel
- Most active users
- Common topics

---

## Next Steps

1. Create Slack app
2. Configure credentials
3. Deploy AskDocs
4. Install to workspace
5. Test in #general

**Support:** slack-support@askdocs.ai
