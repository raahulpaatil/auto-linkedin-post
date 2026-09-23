"""Orchestrates the pipeline: ingest -> screen -> draft -> deliver.

Phase 1 only runs ingest and prints the resulting tracker state. screen/draft/
deliver are wired in as later phases land, guarded by NotImplementedError so
it's obvious what's real and what isn't.
"""

from dotenv import load_dotenv

from src import tracker
from src.ingest import run_ingestion
from src.telegram_client import get_client

load_dotenv()


def main() -> None:
    client = get_client()

    notes = run_ingestion(client)
    print(f"Ingested {len(notes)} note(s):\n")
    for note in notes:
        preview = note["raw_text"][:80]
        print(f"  {note['id']} ({note['type']}): {preview}...")

    print("\nTracker state (data/tracker.json):")
    for note_id, entry in tracker.load_tracker()["notes"].items():
        print(f"  {note_id}: {entry['status']}")


if __name__ == "__main__":
    main()
