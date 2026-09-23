"""Orchestrates the pipeline: ingest -> screen -> draft -> deliver.

All four stages are wired to real logic. Ingest/deliver go through
telegram_client.get_client(), which returns the mock or real client based on
PIPELINE_MODE; screen/draft always call the live Gemini API.
"""

import os

from dotenv import load_dotenv

from src import tracker
from src.deliver import run_delivery
from src.draft import run_drafting
from src.ingest import run_ingestion
from src.screen import run_screening
from src.telegram_client import get_client

load_dotenv()


def main() -> None:
    client = get_client()

    notes = run_ingestion(client)
    print(f"Ingested {len(notes)} note(s):\n")
    for note in notes:
        preview = note["raw_text"][:80]
        print(f"  {note['id']} ({note['type']}): {preview}...")

    screened = run_screening()
    print(f"\nScreened {len(screened)} note(s):\n")
    for note_id, result in screened:
        flag = f" [CONFIDENTIAL: {result['confidential_reason']}]" if result.get("confidential_flag") else ""
        print(f"  {note_id}: {result['decision']} — {result['reason']}{flag}")

    drafted = run_drafting()
    print(f"\nDrafted {len(drafted)} note(s):\n")
    for note_id, draft in drafted:
        print(f"--- {note_id} ---\n{draft}\n")

    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if chat_id and not chat_id.startswith("REPLACE_ME"):
        delivered = run_delivery(client, chat_id)
        print(f"Delivered {len(delivered)} draft(s) via Telegram: {delivered}\n")
    else:
        print("TELEGRAM_CHAT_ID not set — skipping delivery.\n")

    print("Tracker state (data/tracker.json):")
    for note_id, entry in tracker.load_tracker()["notes"].items():
        flags = []
        if entry["confidential_flag"]:
            flags.append("CONFIDENTIAL")
        if entry["delivered"]:
            flags.append("DELIVERED")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        print(f"  {note_id}: {entry['status']}{suffix}")


if __name__ == "__main__":
    main()
