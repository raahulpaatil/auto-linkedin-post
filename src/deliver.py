"""Deliver stage: send a ready draft back to Meera via the Telegram bot, and
mark it delivered in the tracker so a later run doesn't resend it.

Non-negotiable rule 1: this stage only ever sends the draft back to Meera for
her own review and manual posting. It must never call anything that posts to
LinkedIn directly.
"""

from src import tracker


def _format_message(note_id: str, entry: dict) -> str:
    lines = [f"Draft ready: {note_id}", f"Screening note: {entry['reason']}"]
    if entry.get("confidential_flag"):
        lines.append(f"FLAGGED FOR REVIEW: {entry['confidential_reason']}")
    lines.append("")
    lines.append(entry["draft"])
    return "\n".join(lines)


def deliver_draft(client, chat_id: str, note_id: str) -> None:
    entry = tracker.get_note(note_id)
    if entry is None:
        raise KeyError(f"No tracker entry for note {note_id!r}")
    if entry["status"] != "Draft ready":
        raise ValueError(f"Note {note_id!r} is not Draft ready (status={entry['status']!r})")
    client.send_message(chat_id, _format_message(note_id, entry))
    tracker.set_delivered(note_id)


def run_delivery(client, chat_id: str) -> list[str]:
    """Delivers every "Draft ready" note that hasn't been delivered yet."""
    delivered = []
    for note_id, entry in tracker.list_notes(status="Draft ready").items():
        if entry.get("delivered"):
            continue
        deliver_draft(client, chat_id, note_id)
        delivered.append(note_id)
    return delivered
