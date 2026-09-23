"""Deliver stage (phase 4, not yet built): send a ready draft back to Meera via
the Telegram bot, and update the tracker to "Draft ready".

Non-negotiable rule 1: this stage only ever sends the draft back to Meera for
her own review and manual posting. It must never call anything that posts to
LinkedIn directly.
"""

from src import tracker


def deliver_draft(client, chat_id: str, note_id: str, draft_text: str) -> None:
    """Sends draft_text to chat_id via client, then marks the note "Draft ready"
    in the tracker. Not yet implemented — lands in phase 4, once a real
    Telegram bot token is available.
    """
    raise NotImplementedError("Delivery stage not yet built - phase 4")
