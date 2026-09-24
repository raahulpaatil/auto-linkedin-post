"""Ingest stage: capture text and voice notes from Telegram, transcribe voice to
text, store the raw note with a timestamp and source id, and register it in the
tracker with status "New".
"""

from src import storage, tracker
from src.transcribe import transcribe_voice


def _note_path(note_id: str) -> str:
    return f"data/notes/{note_id}.json"


def save_raw_note(note: dict) -> None:
    storage.write_json(_note_path(note["id"]), note, message=f"Ingest {note['id']}")


def load_raw_note(note_id: str) -> dict:
    raw = storage.read_json(_note_path(note_id), default=None)
    if raw is None:
        raise FileNotFoundError(f"No raw note stored for {note_id!r}")
    return raw


def ingest_message(message: dict) -> dict:
    """Turns one incoming Telegram-shaped message into a stored raw note and a
    new tracker entry. Idempotent: re-ingesting the same message_id is a no-op
    on the tracker side (add_note) and just rewrites the same raw note file.
    """
    note_id = f"note_{message['message_id']}"
    source_id = f"telegram:{message['message_id']}"

    if message["type"] == "text":
        raw_text = message["text"]
    elif message["type"] == "voice":
        raw_text = transcribe_voice(
            message["voice_file_id"],
            mock_transcript=message.get("transcript_placeholder"),
        )
    else:
        raise ValueError(f"Unknown message type {message['type']!r}")

    note = {
        "id": note_id,
        "source_id": source_id,
        "timestamp": message["date"],
        "type": message["type"],
        "raw_text": raw_text,
    }
    save_raw_note(note)
    tracker.add_note(
        note_id=note_id,
        timestamp=message["date"],
        source_id=source_id,
        note_type=message["type"],
    )
    return note


def run_ingestion(client) -> list[dict]:
    """Pulls all pending updates from the given Telegram client and ingests each."""
    updates = client.get_updates()
    return [ingest_message(message) for message in updates]
