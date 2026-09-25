"""Draft stage: generate a full LinkedIn-length draft for a "Develop" note,
using voice/meera_voice_skill.md as the system prompt — the style contract
itself (non-negotiable rule 3), not optional background.

Non-negotiable rule 2 applies here: if the note has no real, checkable source
for a statistic or "current news" hook, the draft must contain the exact
literal placeholder "[CURRENT HOOK – Meera to add source]" rather than an
invented citation. Before drafting, we search Google News RSS (src/rss.py)
using the search_query the screening stage produced, to look for a real,
current, checkable source on the note's topic — this extends the citation
rule to sources we actively look for, not just ones already in the note. The
search is best-effort (never blocks drafting) and the model is instructed to
use a result only if it's a genuine, honest fit, never to force one in.
"""

import os

from src import gemini_client, rss, tracker
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
already been screened as worth developing into a LinkedIn post, and possibly \
a list of real news articles found via a Google News search on this note's \
topic. Write the full post now, following the Structural Skeleton and \
Sentence-Level Signatures sections exactly.

Non-negotiable citation rule: if the note itself contains a real, checkable \
external reference (a named institution, a year, a specific figure), use it \
exactly as given — do not alter the number or the source. Otherwise, if a \
candidate news article was provided below and is genuinely, directly \
relevant to the specific claim this post needs to make, you may cite it — \
using the real outlet name, headline, and date exactly as given, and never \
claiming a statistic or finding the article doesn't actually state. If none \
of the candidate articles are a good, honest fit, or none were provided, and \
the note has no source of its own, and the post would naturally reach for a \
statistic or "current research" hook to make its point, insert the exact \
literal placeholder "{CURRENT_HOOK_PLACEHOLDER}" instead of inventing a \
source or a number. Never fabricate a study, statistic, or institution, and \
never soften an invented figure into a vague quantifier to hide that it was \
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


def _format_rss_block(rss_results: list[dict]) -> str:
    lines = [
        "Candidate real news articles found via Google News search on this "
        "note's topic (use only if one is a genuine, direct fit — see the "
        "citation rule above; otherwise ignore all of these):"
    ]
    for r in rss_results:
        source = r.get("source") or "source unknown"
        lines.append(f'- "{r["title"]}" — {source}, {r.get("published", "date unknown")} ({r["link"]})')
    return "\n".join(lines)


def draft_post(raw_text: str, rss_results: list[dict] | None = None) -> str:
    system_instruction = f"{load_voice_skill()}\n\n---\n\n{DRAFTING_INSTRUCTIONS}"
    prompt = raw_text
    if rss_results:
        prompt = f"{raw_text}\n\n---\n\n{_format_rss_block(rss_results)}"
    draft = gemini_client.generate(
        prompt=prompt,
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
        entry = tracker.get_note(note_id)
        search_query = entry.get("search_query") if entry else None
        rss_results = rss.search_google_news(search_query) if search_query else []
        draft = draft_post(note["raw_text"], rss_results=rss_results)
        tracker.set_draft(note_id, draft)
        results.append((note_id, draft))
    return results
