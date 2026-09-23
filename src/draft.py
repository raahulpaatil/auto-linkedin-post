"""Draft stage (phase 3, not yet built): generate a full LinkedIn-length draft
from a "Develop" note, using voice/meera_voice_skill.md as the system prompt —
not optional background, the style contract itself (non-negotiable rule 3).

Non-negotiable rule 2 applies here: if the note has no real, checkable source
for a statistic or "current news" hook, the draft must contain the exact
literal placeholder "[CURRENT HOOK – Meera to add source]" rather than an
invented citation.
"""

import os

from src import gemini_client  # noqa: F401  (wired up in phase 3)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE_SKILL_PATH = os.path.join(BASE_DIR, "voice", "meera_voice_skill.md")


def load_voice_skill() -> str:
    with open(VOICE_SKILL_PATH, "r", encoding="utf-8") as f:
        return f.read()


def draft_post(raw_text: str) -> str:
    """Returns a full LinkedIn-length draft in Meera's voice. Not yet
    implemented — lands in phase 3.
    """
    raise NotImplementedError("Drafting stage not yet built - phase 3")
