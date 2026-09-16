"""Remote MCP server exposing Reddit direct-message tools.

Connect this to Grok (grok.com/connectors -> Add Connector -> Custom) as a
"Bring Your Own MCP" server so Grok can read and reply to your Reddit DMs
using your existing Grok subscription -- no separate LLM API key needed.

Required environment variables:
    REDDIT_CLIENT_ID       - Reddit app client id (script-type app)
    REDDIT_CLIENT_SECRET   - Reddit app client secret
    REDDIT_USERNAME        - Reddit account username
    REDDIT_PASSWORD        - Reddit account password

Optional environment variables:
    REDDIT_USER_AGENT      - defaults to "reddit-dm-mcp/1.0 (by u/<username>)"
    MCP_AUTH_TOKEN         - if set, requires "Authorization: Bearer <token>"
                              on every request. Strongly recommended once
                              this server is reachable on the public
                              internet (e.g. via a tunnel), since anyone
                              with the URL could otherwise read/send your
                              Reddit DMs.
    MCP_HOST               - defaults to "0.0.0.0"
    MCP_PORT               - defaults to 8000
"""

import os

import praw
from mcp.server.mcpserver import MCPServer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = MCPServer("reddit-dm")


def _client() -> praw.Reddit:
    username = os.environ["REDDIT_USERNAME"]
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=username,
        password=os.environ["REDDIT_PASSWORD"],
        user_agent=os.environ.get(
            "REDDIT_USER_AGENT", f"reddit-dm-mcp/1.0 (by u/{username})"
        ),
    )


@mcp.tool()
def list_unread_dms(limit: int = 25) -> list[dict]:
    """List unread Reddit direct messages (excludes comment replies/mentions)."""
    reddit = _client()
    return [
        {
            "id": msg.id,
            "author": msg.author.name if msg.author else None,
            "subject": msg.subject,
            "body": msg.body,
            "created_utc": msg.created_utc,
        }
        for msg in reddit.inbox.unread(limit=limit)
        if isinstance(msg, praw.models.Message)
    ]


@mcp.tool()
def reply_dm(message_id: str, body: str) -> dict:
    """Reply to a Reddit DM by its message id, then mark it read."""
    reddit = _client()
    message = reddit.inbox.message(message_id)
    reply = message.reply(body)
    message.mark_read()
    return {"status": "sent", "reply_id": reply.id}


@mcp.tool()
def send_dm(username: str, subject: str, body: str) -> dict:
    """Send a new Reddit direct message to a user."""
    reddit = _client()
    reddit.redditor(username).message(subject=subject, message=body)
    return {"status": "sent", "to": username}


@mcp.tool()
def mark_all_read() -> dict:
    """Mark every unread message in the inbox as read."""
    reddit = _client()
    reddit.inbox.mark_all_read()
    return {"status": "ok"}


class BearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str):
        super().__init__(app)
        self._token = token

    async def dispatch(self, request: Request, call_next):
        if request.headers.get("authorization") != f"Bearer {self._token}":
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


def build_app():
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    app = mcp.streamable_http_app(host=host)
    token = os.environ.get("MCP_AUTH_TOKEN")
    if token:
        app.add_middleware(BearerAuthMiddleware, token=token)
    else:
        print(
            "WARNING: MCP_AUTH_TOKEN is not set -- this server accepts "
            "unauthenticated requests. Set MCP_AUTH_TOKEN before exposing "
            "it on the public internet."
        )
    return app


if __name__ == "__main__":
    import uvicorn

    # Most PaaS hosts (Render, Railway, Heroku) inject PORT to bind to.
    port = int(os.environ.get("PORT") or os.environ.get("MCP_PORT", "8000"))
    uvicorn.run(
        build_app(),
        host=os.environ.get("MCP_HOST", "0.0.0.0"),
        port=port,
    )
