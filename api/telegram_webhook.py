"""Vercel serverless entry point (deployed at /api/telegram_webhook).

Telegram calls this URL directly, once per message, after `setWebhook` is
registered — this replaces the local polling loop (main.py) for the
always-on deployment. Requires STORAGE_BACKEND=github, PIPELINE_MODE=live,
and TELEGRAM_BOT_TOKEN / GEMINI_API_KEY / TELEGRAM_CHAT_ID / GITHUB_TOKEN /
GITHUB_REPO set as Vercel environment variables.

Known limitation: on an error partway through (e.g. a Gemini call fails), we
still ack with 200 rather than let Telegram retry, to avoid reprocessing a
note that already partially succeeded (e.g. drafted but not yet delivered).
That means a mid-pipeline failure is only visible in the Vercel function
logs, not retried automatically. Acceptable for a solo, low-volume channel.

Also: drafts get delivered back into this same channel, so the bot's own
post is itself a channel_post update this webhook would otherwise receive.
ingest_message() (src/ingest.py) guards against re-ingesting it as a new
note — see its docstring for the known gap with multi-chunk drafts.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import tracker  # noqa: E402
from src.deliver import deliver_draft  # noqa: E402
from src.draft import draft_post  # noqa: E402
from src.ingest import ingest_message  # noqa: E402
from src.screen import DECISION_TO_STATUS, screen_note  # noqa: E402
from src.telegram_client import RealTelegramClient, extract_message  # noqa: E402


def process_update(update: dict) -> str | None:
    """Runs one Telegram update through ingest -> screen -> (draft -> deliver
    if Develop). Returns the note_id processed, or None if this update wasn't
    a text/voice message we ingest (including our own delivered drafts
    looping back through the channel).
    """
    message = extract_message(update)
    if message is None:
        return None

    note = ingest_message(message)
    if note is None:
        return None

    result = screen_note(note["raw_text"])
    status = DECISION_TO_STATUS[result["decision"]]
    tracker.set_status(note["id"], status, reason=result["reason"])
    tracker.set_confidential_flag(
        note["id"],
        flagged=result.get("confidential_flag", False),
        reason=result.get("confidential_reason"),
    )

    if result["decision"] != "Develop":
        return note["id"]

    draft = draft_post(note["raw_text"])
    tracker.set_draft(note["id"], draft)

    client = RealTelegramClient()
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    deliver_draft(client, chat_id, note["id"])
    return note["id"]


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            update = json.loads(body)
            note_id = process_update(update)
            print(f"Processed update, note_id={note_id}")
        except Exception as exc:  # noqa: BLE001 — must always ack Telegram
            print(f"Error processing update: {exc!r}")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Skinstinct pipeline webhook is running.")
