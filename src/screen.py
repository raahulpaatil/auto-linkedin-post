"""Screen stage (phase 2, not yet built): classify a raw note as
Develop / Park / Discard with a one-line reason, and set the confidentiality
flag (non-negotiable rule 4 — flag notes with manufacturing detail or
identifiable customer info so they never reach a public draft unreviewed).
"""

from src import gemini_client  # noqa: F401  (wired up in phase 2)


def screen_note(raw_text: str) -> dict:
    """Returns {"decision": "Develop"|"Park"|"Discard", "reason": str,
    "confidential_flag": bool}. Not yet implemented — lands in phase 2.
    """
    raise NotImplementedError("Screening stage not yet built - phase 2")
