"""Reddit DM bot that replies using xAI's Grok API.

Polls the authenticated Reddit account's inbox for new private messages
and replies to each one with a Grok-generated response.

Required environment variables:
    REDDIT_CLIENT_ID       - Reddit app client id (script-type app)
    REDDIT_CLIENT_SECRET   - Reddit app client secret
    REDDIT_USERNAME        - Reddit account username
    REDDIT_PASSWORD        - Reddit account password
    XAI_API_KEY            - xAI API key for Grok

Optional environment variables:
    REDDIT_USER_AGENT      - defaults to "reddit-grok-dm-bot/1.0 (by u/<username>)"
    GROK_MODEL             - defaults to "grok-4"
    GROK_SYSTEM_PROMPT     - system prompt steering Grok's replies
    XAI_BASE_URL           - defaults to "https://api.x.ai/v1"
    POLL_INTERVAL_SECONDS  - defaults to 30
"""

import logging
import os
import time

import praw
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("reddit_grok_bot")

GROK_MODEL = os.environ.get("GROK_MODEL", "grok-4")
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "30"))
SYSTEM_PROMPT = os.environ.get(
    "GROK_SYSTEM_PROMPT",
    "You are replying to Reddit direct messages on behalf of the account owner. "
    "Keep replies concise, friendly, and in plain text or Reddit markdown.",
)


def build_reddit_client() -> praw.Reddit:
    username = os.environ["REDDIT_USERNAME"]
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=username,
        password=os.environ["REDDIT_PASSWORD"],
        user_agent=os.environ.get(
            "REDDIT_USER_AGENT", f"reddit-grok-dm-bot/1.0 (by u/{username})"
        ),
    )


def build_grok_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["XAI_API_KEY"],
        base_url=os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1"),
    )


def generate_reply(grok: OpenAI, message_body: str) -> str:
    response = grok.chat.completions.create(
        model=GROK_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message_body},
        ],
    )
    return response.choices[0].message.content.strip()


def handle_message(grok: OpenAI, message: praw.models.Message) -> None:
    if not isinstance(message, praw.models.Message):
        # Comment replies / username mentions also show up in the inbox stream.
        message.mark_read()
        return

    if message.author is None:
        message.mark_read()
        return

    logger.info("New DM from u/%s: %s", message.author.name, message.body[:80])

    try:
        reply_text = generate_reply(grok, message.body)
        message.reply(reply_text)
        logger.info("Replied to u/%s", message.author.name)
    except Exception:
        logger.exception("Failed to handle message from u/%s", message.author.name)
    finally:
        message.mark_read()


def main() -> None:
    reddit = build_reddit_client()
    grok = build_grok_client()
    logger.info("Logged in to Reddit as u/%s", reddit.user.me())
    logger.info("Watching for new DMs (polling every %ss)...", POLL_INTERVAL_SECONDS)

    for message in reddit.inbox.stream(pause_after=-1):
        if message is None:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        handle_message(grok, message)


if __name__ == "__main__":
    main()
