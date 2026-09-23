"""Reads and writes data/tracker.json — the status table for every ingested note.

Storage is a single JSON file committed to the repo (not a database), per the
project's decision to use git as lightweight storage for a solo-user pipeline.
"""

import json
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_PATH = os.path.join(BASE_DIR, "data", "tracker.json")

VALID_STATUSES = {"New", "Developing", "Parked", "Discarded", "Draft ready"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_tracker() -> dict:
    if not os.path.exists(TRACKER_PATH):
        return {"notes": {}}
    with open(TRACKER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tracker(tracker: dict) -> None:
    os.makedirs(os.path.dirname(TRACKER_PATH), exist_ok=True)
    with open(TRACKER_PATH, "w", encoding="utf-8") as f:
        json.dump(tracker, f, indent=2, ensure_ascii=False)
        f.write("\n")


def add_note(note_id: str, timestamp: str, source_id: str, note_type: str) -> dict:
    tracker = load_tracker()
    if note_id in tracker["notes"]:
        return tracker["notes"][note_id]
    entry = {
        "status": "New",
        "reason": None,
        "confidential_flag": False,
        "confidential_reason": None,
        "source_id": source_id,
        "note_type": note_type,
        "draft": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    tracker["notes"][note_id] = entry
    save_tracker(tracker)
    return entry


def set_status(note_id: str, status: str, reason: str | None = None) -> dict:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status {status!r}, must be one of {VALID_STATUSES}")
    tracker = load_tracker()
    if note_id not in tracker["notes"]:
        raise KeyError(f"No tracker entry for note {note_id!r}")
    entry = tracker["notes"][note_id]
    entry["status"] = status
    if reason is not None:
        entry["reason"] = reason
    entry["updated_at"] = _now()
    save_tracker(tracker)
    return entry


def set_confidential_flag(note_id: str, flagged: bool, reason: str | None = None) -> dict:
    tracker = load_tracker()
    if note_id not in tracker["notes"]:
        raise KeyError(f"No tracker entry for note {note_id!r}")
    entry = tracker["notes"][note_id]
    entry["confidential_flag"] = flagged
    entry["confidential_reason"] = reason
    entry["updated_at"] = _now()
    save_tracker(tracker)
    return entry


def set_draft(note_id: str, draft_text: str) -> dict:
    tracker = load_tracker()
    if note_id not in tracker["notes"]:
        raise KeyError(f"No tracker entry for note {note_id!r}")
    entry = tracker["notes"][note_id]
    entry["draft"] = draft_text
    entry["status"] = "Draft ready"
    entry["updated_at"] = _now()
    save_tracker(tracker)
    return entry


def get_note(note_id: str) -> dict | None:
    return load_tracker()["notes"].get(note_id)


def list_notes(status: str | None = None) -> dict:
    notes = load_tracker()["notes"]
    if status is None:
        return notes
    return {nid: entry for nid, entry in notes.items() if entry["status"] == status}
