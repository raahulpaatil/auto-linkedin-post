"""Deliver stage: send Meera a Telegram message for every screened note
(decision, 8 metrics, bucket reasoning) and, for "Develop" notes once
drafted, the full draft — then mark each as delivered so a later run doesn't
resend it.

Non-negotiable rule 1: drafts only ever go back to Meera for her own review
and manual posting. This stage must never call anything that posts to
LinkedIn directly.
"""

from src import tracker
from src.constants import DELIVERY_MESSAGE_PREFIX, METRIC_KEYS, SCREENING_MESSAGE_PREFIX


def _format_screening_message(note_id: str, entry: dict) -> str:
    lines = [
        f"{SCREENING_MESSAGE_PREFIX} {note_id}",
        f"Decision: {entry['status']}",
        entry["reason"],
        "",
        "Metrics (1-5):",
    ]
    metrics = entry.get("metrics") or {}
    for key in METRIC_KEYS:
        if key in metrics:
            lines.append(f"  {key}: {metrics[key]}")
    lines.append("")
    lines.append(entry["bucket_explanation"])
    if entry.get("confidential_flag"):
        lines.append("")
        lines.append(f"FLAGGED FOR REVIEW: {entry['confidential_reason']}")
    return "\n".join(lines)


def _format_draft_message(note_id: str, entry: dict) -> str:
    return f"{DELIVERY_MESSAGE_PREFIX} {note_id}\n\n{entry['draft']}"


def deliver_screening_result(client, chat_id: str, note_id: str) -> None:
    entry = tracker.get_note(note_id)
    if entry is None:
        raise KeyError(f"No tracker entry for note {note_id!r}")
    client.send_message(chat_id, _format_screening_message(note_id, entry))
    tracker.set_screening_delivered(note_id)


def run_screening_delivery(client, chat_id: str) -> list[str]:
    """Delivers the screening result (decision, metrics, bucket reasoning)
    for every note that's been screened but not yet had that result sent —
    regardless of which bucket it landed in.
    """
    delivered = []
    for note_id, entry in tracker.list_notes().items():
        if entry["status"] == "New" or entry.get("screening_delivered"):
            continue
        deliver_screening_result(client, chat_id, note_id)
        delivered.append(note_id)
    return delivered


def deliver_draft(client, chat_id: str, note_id: str) -> None:
    entry = tracker.get_note(note_id)
    if entry is None:
        raise KeyError(f"No tracker entry for note {note_id!r}")
    if entry["status"] != "Draft ready":
        raise ValueError(f"Note {note_id!r} is not Draft ready (status={entry['status']!r})")
    client.send_message(chat_id, _format_draft_message(note_id, entry))
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
