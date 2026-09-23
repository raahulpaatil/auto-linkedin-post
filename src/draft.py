"""Draft stage: generate a full LinkedIn-length draft for a "Develop" note,
using voice/meera_voice_skill.md as the system prompt — the style contract
itself (non-negotiable rule 3), not optional background.

Non-negotiable rule 2 applies here: if the note has no real, checkable source
for a statistic or "current news" hook, the draft must contain the exact
literal placeholder "[CURRENT HOOK – Meera to add source]" rather than an
invented citation.
"""

import os

from src import gemini_client, tracker
from src.ingest import load_raw_note

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE_SKILL_PATH = os.path.join(BASE_DIR, "voice", "meera_voice_skill.md")

CURRENT_HOOK_PLACEHOLDER = "[CURRENT HOOK – Meera to add source]"

DRAFTING_INSTRUCTIONS = f"""\
You are the drafting stage of a private content pipeline for Meera Pillai, \
founder of the skincare brand Skinstinct. The voice skill document above is \
your style contract, not optional background — every non-negotiable, \
structural move, sentence-level signature, and language rule in it applies \
to what you write.

You will be given one raw note from Meera's Telegram channel that has \
already been screened as worth developing into a LinkedIn post. Write the \
full post now, following the Structural Skeleton and Sentence-Level \
Signatures sections exactly.

Non-negotiable citation rule: if the note contains a real, checkable \
external reference (a named institution, a year, a specific figure), use it \
exactly as given — do not alter the number or the source. If the note does \
not contain one, and the post would naturally reach for a statistic or \
"current research" hook to make its point, insert the exact literal \
placeholder "{CURRENT_HOOK_PLACEHOLDER}" instead of inventing a source or a \
number. Never fabricate a study, statistic, or institution, and never \
soften an invented figure into a vague quantifier to hide that it was \
invented — omit it or use the placeholder instead.

Before you finalise, score your draft against the Pre-Publish Checklist in \
the voice skill document above. If it fails more than one item, revise it \
before responding.

Output only the finished LinkedIn post text. No title, no markdown \
formatting, no preamble, no meta-commentary about the draft.
"""


def load_voice_skill() -> str:
    with open(VOICE_SKILL_PATH, "r", encoding="utf-8") as f:
        return f.read()


def draft_post(raw_text: str) -> str:
    system_instruction = f"{load_voice_skill()}\n\n---\n\n{DRAFTING_INSTRUCTIONS}"
    draft = gemini_client.generate(
        prompt=raw_text,
        system_instruction=system_instruction,
        temperature=0.7,
    )
    return draft.strip()


def run_drafting() -> list[tuple[str, str]]:
    """Drafts every note currently in tracker status "Developing" and updates
    the tracker with the resulting draft (which also flips status to
    "Draft ready"). Confidentiality-flagged notes are still drafted — the
    flag exists so Meera reviews them with that context, not to silently
    skip content she may want to write in an anonymised way.
    """
    results = []
    for note_id in list(tracker.list_notes(status="Developing").keys()):
        note = load_raw_note(note_id)
        draft = draft_post(note["raw_text"])
        tracker.set_draft(note_id, draft)
        results.append((note_id, draft))
    return results
