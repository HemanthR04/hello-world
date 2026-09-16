# reddit-grok-dm-bot

Polls a Reddit account's inbox for new direct messages and replies to each
one using xAI's Grok API.

## Setup

1. Create a Reddit "script" app at https://www.reddit.com/prefs/apps
   (note the client id under the app name, and the secret).
2. Get an xAI API key from https://console.x.ai.
3. Copy `.env.example` to `.env` and fill in your credentials.
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Load the env file and run the bot:

   ```bash
   export $(grep -v '^#' .env | xargs)
   python bot.py
   ```

## Notes

- Only direct messages are answered automatically; comment replies and
  username mentions in the inbox are marked read and skipped.
- The bot logs in with a Reddit username/password (script-app auth), so use
  a dedicated account or an app password if your account has 2FA.
- Tune the reply behavior with `GROK_MODEL` and `GROK_SYSTEM_PROMPT` in
  `.env`.
- This runs as a long-lived process (polling loop) — deploy it somewhere
  that stays up (a small VM, container, or systemd service), it isn't a
  one-shot script.
