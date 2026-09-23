"""Telegram access, behind one interface so ingest/deliver don't care which
implementation is live.

MockTelegramClient reads fake updates from a local JSON file and prints instead
of sending, so the pipeline can be built and tested before Meera provides a real
bot token. RealTelegramClient is the phase-4 replacement.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SAMPLE_PATH = os.path.join(BASE_DIR, "tests", "sample_messages.json")


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
    """Not yet wired. Needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (phase 4)."""

    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
        if not self.token or self.token.startswith("REPLACE_ME"):
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is not set. Add a real token to .env before "
                "using RealTelegramClient."
            )

    def get_updates(self) -> list[dict]:
        raise NotImplementedError("Real Telegram polling lands in phase 4.")

    def send_message(self, chat_id: str, text: str) -> None:
        raise NotImplementedError("Real Telegram delivery lands in phase 4.")

    def download_voice_file(self, file_id: str) -> bytes:
        raise NotImplementedError("Real Telegram voice download lands in phase 4.")


def get_client():
    """Picks mock vs real based on PIPELINE_MODE (defaults to mock)."""
    mode = os.environ.get("PIPELINE_MODE", "mock")
    if mode == "mock":
        return MockTelegramClient()
    return RealTelegramClient()
