"""Reads and writes data/tracker.json — the status table for every ingested note.

Storage is a single JSON file, not a database, per the project's decision to
use git as lightweight storage for a solo-user pipeline. Goes through
src/storage.py, which reads/writes it locally for local dev or via the
GitHub API for the deployed webhook (see storage.py for why).
"""

from datetime import datetime, timezone

from src import storage

TRACKER_PATH = "data/tracker.json"

VALID_STATUSES = {"New", "Developing", "Parked", "Discarded", "Draft ready"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_tracker() -> dict:
    return storage.read_json(TRACKER_PATH, default={"notes": {}})


def save_tracker(tracker: dict, message: str = "Update tracker") -> None:
    storage.write_json(TRACKER_PATH, tracker, message=message)


def add_note(note_id: str, timestamp: str, source_id: str, note_type: str) -> dict:
    tracker = load_tracker()
    if note_id in tracker["notes"]:
        return tracker["notes"][note_id]
    entry = {
        "status": "New",
        "reason": None,
        "bucket_explanation": None,
        "metrics": {},
        "search_query": None,
        "confidential_flag": False,
        "confidential_reason": None,
        "source_id": source_id,
        "note_type": note_type,
        "draft": None,
        "screening_delivered": False,
        "delivered": False,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    tracker["notes"][note_id] = entry
    save_tracker(tracker, message=f"Track {note_id} (New)")
    return entry


def set_screening_result(
    note_id: str,
    status: str,
    reason: str,
    bucket_explanation: str,
    metrics: dict,
    confidential_flag: bool,
    confidential_reason: str | None = None,
    search_query: str | None = None,
) -> dict:
    """Writes the full screening outcome (status, reason, metrics, bucket
    explanation, confidentiality flag, search query) in a single save — one
    GitHub commit on the github storage backend.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status {status!r}, must be one of {VALID_STATUSES}")
    tracker = load_tracker()
    if note_id not in tracker["notes"]:
        raise KeyError(f"No tracker entry for note {note_id!r}")
    entry = tracker["notes"][note_id]
    entry["status"] = status
    entry["reason"] = reason
    entry["bucket_explanation"] = bucket_explanation
    entry["metrics"] = metrics
    entry["search_query"] = search_query
    entry["confidential_flag"] = confidential_flag
    entry["confidential_reason"] = confidential_reason
    entry["updated_at"] = _now()
    save_tracker(tracker, message=f"{note_id}: screened -> {status}")
    return entry


def set_screening_delivered(note_id: str) -> dict:
    tracker = load_tracker()
    if note_id not in tracker["notes"]:
        raise KeyError(f"No tracker entry for note {note_id!r}")
    entry = tracker["notes"][note_id]
    entry["screening_delivered"] = True
    entry["updated_at"] = _now()
    save_tracker(tracker, message=f"{note_id}: screening result delivered")
    return entry


def set_draft(note_id: str, draft_text: str) -> dict:
    tracker = load_tracker()
    if note_id not in tracker["notes"]:
        raise KeyError(f"No tracker entry for note {note_id!r}")
    entry = tracker["notes"][note_id]
    entry["draft"] = draft_text
    entry["status"] = "Draft ready"
    entry["updated_at"] = _now()
    save_tracker(tracker, message=f"{note_id}: draft ready")
    return entry


def set_delivered(note_id: str) -> dict:
    tracker = load_tracker()
    if note_id not in tracker["notes"]:
        raise KeyError(f"No tracker entry for note {note_id!r}")
    entry = tracker["notes"][note_id]
    entry["delivered"] = True
    entry["updated_at"] = _now()
    save_tracker(tracker, message=f"{note_id}: delivered")
    return entry


def get_note(note_id: str) -> dict | None:
    return load_tracker()["notes"].get(note_id)


def list_notes(status: str | None = None) -> dict:
    notes = load_tracker()["notes"]
    if status is None:
        return notes
    return {nid: entry for nid, entry in notes.items() if entry["status"] == status}
