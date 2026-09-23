"""Orchestrates the pipeline: ingest -> screen -> draft -> deliver.

Ingest and screen are wired to real logic (screen calls the live Gemini API).
draft/deliver are wired in as later phases land, guarded by NotImplementedError
so it's obvious what's real and what isn't.
"""

from dotenv import load_dotenv

from src import tracker
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

    print("\nTracker state (data/tracker.json):")
    for note_id, entry in tracker.load_tracker()["notes"].items():
        print(f"  {note_id}: {entry['status']}" + (" [CONFIDENTIAL]" if entry["confidential_flag"] else ""))


if __name__ == "__main__":
    main()
