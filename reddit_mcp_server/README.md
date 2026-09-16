# reddit-dm-mcp

A remote MCP server exposing Reddit direct-message tools, meant to be added
to Grok as a **custom connector** (grok.com/connectors -> Add Connector ->
Custom -> "Bring Your Own MCP"). Grok calls these tools directly using your
existing subscription -- there's no separate LLM API bill for this.

## Cost

- **Reddit API**: free for this kind of personal, low-volume script-app use.
- **Grok**: your existing subscription covers the model calls; custom
  connectors require a paid Grok tier (which you already have).
- **Hosting**: $0 if you run it locally behind a free tunnel (see below), or
  the free tier of most small app hosts if you want it always-on.

## Tools exposed

- `list_unread_dms(limit=25)` - list unread DMs (comment replies/mentions
  in the inbox are excluded)
- `reply_dm(message_id, body)` - reply to a DM, marks it read
- `send_dm(username, subject, body)` - start a new DM to someone
- `mark_all_read()` - clear the unread inbox

## Setup (with a computer + terminal)

1. Create a Reddit "script" app at https://www.reddit.com/prefs/apps
   (note the client id under the app name, and the secret).
2. Copy `.env.example` to `.env`, fill in your Reddit credentials, and set
   `MCP_AUTH_TOKEN` to a random secret (anyone with your server's URL and
   this token can read/send your Reddit DMs, so don't skip it):

   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. Install dependencies and run:

   ```bash
   pip install -r requirements.txt
   export $(grep -v '^#' .env | xargs)
   python server.py
   ```

   This starts a streamable-HTTP MCP server on `http://0.0.0.0:8000/mcp`
   (it also respects a `PORT` env var, for PaaS hosts that set one).

4. Expose it to the public internet so Grok can reach it. For local
   testing, a tunnel is the quickest option:

   ```bash
   # ngrok
   ngrok http 8000

   # or Cloudflare Tunnel (no account needed for a quick tunnel)
   cloudflared tunnel --url http://localhost:8000
   ```

   For anything long-lived, deploy `server.py` to a small host/container
   instead of leaving a laptop tunnel running.

5. In Grok, go to grok.com/connectors -> Add Connector -> Custom, and enter:
   - **Server URL**: `https://<your-tunnel-or-host>/mcp`
   - **Authorization header**: `Bearer <the MCP_AUTH_TOKEN you set>`

Once connected, you can ask Grok things like "check my Reddit DMs and draft
replies" and it will call these tools directly.

## Setup (phone only, no computer -- deploy on Render)

Render's free web-service tier builds straight from a GitHub repo, so
everything below is doable from Safari on an iPhone.

1. **Create the Reddit app** at https://www.reddit.com/prefs/apps in
   Safari (choose "script" type). Note the client id (under the app name)
   and secret.
2. **Pick an auth token** -- any long random string you make up works
   (e.g. mash your keyboard for 30+ characters). You'll paste this into
   both Render and Grok.
3. **Sign up at https://render.com** (GitHub login is easiest).
4. **New -> Web Service -> Build and deploy from a Git repository**,
   connect your `hello-world` repo, branch
   `claude/review-shared-conversation-nlk330` (or `main` once merged).
5. Configure the service:
   - **Root Directory**: `reddit_mcp_server`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
   - **Instance Type**: Free
6. Under **Environment**, add these variables:
   - `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`,
     `REDDIT_PASSWORD` -- from step 1
   - `MCP_AUTH_TOKEN` -- from step 2

   (Render sets `PORT` itself -- leave that one alone, `server.py` reads
   it automatically.)
7. **Deploy.** Render gives you a URL like
   `https://reddit-dm-mcp.onrender.com`.
8. In Grok (grok.com/connectors in Safari, or the connector settings in
   the iOS app), **Add Connector -> Custom**:
   - **Server URL**: `https://reddit-dm-mcp.onrender.com/mcp`
   - **Authorization header**: `Bearer <the MCP_AUTH_TOKEN from step 2>`

Free Render web services spin down after inactivity and take a few
seconds to wake on the next request -- fine here, since this server only
does something when Grok calls it, it isn't polling in the background.
