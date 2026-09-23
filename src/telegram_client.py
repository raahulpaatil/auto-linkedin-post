"""Telegram access, behind one interface so ingest/deliver don't care which
implementation is live.

MockTelegramClient reads fake updates from a local JSON file and prints instead
of sending, for offline development. RealTelegramClient talks to the real
Telegram Bot API over plain HTTP (no extra SDK — sendMessage/getUpdates/getFile
are simple enough that a thin wrapper is clearer than pulling in a full bot
framework).
"""

import json
import os
from datetime import datetime, timezone

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SAMPLE_PATH = os.path.join(BASE_DIR, "tests", "sample_messages.json")
OFFSET_PATH = os.path.join(BASE_DIR, "data", "telegram_offset.json")

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"
TELEGRAM_FILE_BASE = "https://api.telegram.org/file/bot{token}/{file_path}"
MAX_MESSAGE_LENGTH = 4096


class MockTelegramClient:
    def __init__(self, sample_path: str = DEFAULT_SAMPLE_PATH):
        self.sample_path = sample_path

    def get_updates(self) -> list[dict]:
        """Returns the fake incoming messages, shaped like Telegram updates."""
        with open(self.sample_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def send_message(self, chat_id: str, text: str) -> None:
        print(f"[MOCK TELEGRAM SEND] to {chat_id}:\n{text}\n")

    def download_voice_file(self, file_id: str) -> bytes:
        raise NotImplementedError(
            "MockTelegramClient does not hold real audio bytes — voice notes in "
            "mock mode are resolved via their 'transcript_placeholder' field instead."
        )


class RealTelegramClient:
    """Talks to the real Telegram Bot API. Needs TELEGRAM_BOT_TOKEN."""

    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
        if not self.token or self.token.startswith("REPLACE_ME"):
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is not set. Add a real token to .env before "
                "using RealTelegramClient."
            )

    def _call(self, method: str, **params) -> dict | list:
        url = TELEGRAM_API_BASE.format(token=self.token, method=method)
        response = requests.post(url, json=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error on {method}: {data}")
        return data["result"]

    def _load_offset(self) -> int:
        if not os.path.exists(OFFSET_PATH):
            return 0
        with open(OFFSET_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("last_update_id", 0)

    def _save_offset(self, next_update_id: int) -> None:
        os.makedirs(os.path.dirname(OFFSET_PATH), exist_ok=True)
        with open(OFFSET_PATH, "w", encoding="utf-8") as f:
            json.dump({"last_update_id": next_update_id}, f, indent=2)
            f.write("\n")

    def get_updates(self) -> list[dict]:
        """Fetches Telegram updates since the last processed one and returns
        them normalised to the shape ingest.py expects (message_id/date/type
        plus text or voice_file_id). Advances and persists the offset so a
        later call doesn't re-fetch what's already been ingested.
        """
        offset = self._load_offset()
        raw_updates = self._call("getUpdates", offset=offset, timeout=10)
        messages = []
        highest_update_id = offset - 1
        for update in raw_updates:
            highest_update_id = max(highest_update_id, update["update_id"])
            msg = update.get("channel_post") or update.get("message")
            if msg is None:
                continue  # edits, reactions, other update types we don't ingest
            if "voice" in msg:
                messages.append(
                    {
                        "message_id": msg["message_id"],
                        "date": _unix_to_iso(msg["date"]),
                        "type": "voice",
                        "voice_file_id": msg["voice"]["file_id"],
                    }
                )
            elif "text" in msg:
                messages.append(
                    {
                        "message_id": msg["message_id"],
                        "date": _unix_to_iso(msg["date"]),
                        "type": "text",
                        "text": msg["text"],
                    }
                )
            # other message types (photos, stickers, etc.) are ignored
        if raw_updates:
            self._save_offset(highest_update_id + 1)
        return messages

    def send_message(self, chat_id: str, text: str) -> None:
        for chunk in _split_message(text):
            self._call("sendMessage", chat_id=chat_id, text=chunk)

    def download_voice_file(self, file_id: str) -> bytes:
        file_info = self._call("getFile", file_id=file_id)
        url = TELEGRAM_FILE_BASE.format(token=self.token, file_path=file_info["file_path"])
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content


def _unix_to_iso(unix_ts: int) -> str:
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()


def _split_message(text: str, limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    if len(text) <= limit:
        return [text]
    return [text[i : i + limit] for i in range(0, len(text), limit)]


def get_client():
    """Picks mock vs real based on PIPELINE_MODE (defaults to mock)."""
    mode = os.environ.get("PIPELINE_MODE", "mock")
    if mode == "mock":
        return MockTelegramClient()
    return RealTelegramClient()
