"""Screen stage: classify a raw note as Develop / Park / Discard with a
one-line reason, and set the confidentiality flag (non-negotiable rule 4 —
flag notes with manufacturing detail or identifiable customer info so they
never reach a public draft unreviewed).
"""

import json

from src import gemini_client, tracker
from src.ingest import load_raw_note

VALID_DECISIONS = {"Develop", "Park", "Discard"}

DECISION_TO_STATUS = {
    "Develop": "Developing",
    "Park": "Parked",
    "Discard": "Discarded",
}

SYSTEM_INSTRUCTION = """\
You are the screening stage of a private content pipeline for Meera Pillai, \
founder of the skincare brand Skinstinct. You triage one raw note from her \
Telegram channel. You do not write any content — you only classify.

Classify the note into exactly one decision:
- "Develop": the note has enough concrete substance (a specific fact, number, \
  moment, or mechanism) to become a strong LinkedIn post, and fits one of \
  Meera's recurring topics: Ingredient Deep-Dive, Formulation Science, \
  Founder Story, India-Specific Context, Industry Transparency, Consumer \
  Education, or Brand Philosophy.
- "Park": the note is on-topic but too thin, vague, or unfinished to draft \
  from yet — it might become a post later with more detail.
- "Discard": the note is personal, unrelated to Skinstinct/skincare, or has \
  no usable content angle (reminders, errands, unrelated chatter).

Independently of the decision, set confidential_flag to true if the note \
contains either of these, and only these:
- Specific internal manufacturing/formulation detail that goes beyond what \
  Meera would already say publicly (e.g. exact supplier names, unreleased \
  formulation ratios, internal batch/QC failure specifics).
- Identifiable customer information (a name, contact detail, address, or an \
  order/batch number tied to a specific named or otherwise identifiable \
  customer).

The confidentiality check is mandatory on every note, completely independent \
of the decision — including notes you decide to "Discard". A note about an \
individual customer's order, complaint, or reaction (a name, an email \
address, a physical address, a phone number, or an order/batch number tied \
to that person) is confidential even when it is not post-worthy content at \
all. Do not let "this isn't a content idea" cause you to skip the \
confidentiality check.

Example: a note reading "customer emailed her address, said she reacted to \
the serum, need her batch number" is decision "Discard" (it's a customer \
service task, not a content idea) AND confidential_flag true \
(confidential_reason: "identifiable customer contact and reaction detail").

A note can also be both "Develop" and confidential — that means the \
underlying topic is worth a post, but the specific sensitive detail must be \
stripped or reviewed by Meera before drafting. Set confidential_reason to a \
short phrase naming what triggered the flag, or null if confidential_flag is \
false.

Never invent facts not present in the note. Base every field only on the \
note text given to you.

Respond with strict JSON only, no markdown fencing, matching exactly:
{"decision": "Develop" | "Park" | "Discard", "reason": "<one sentence, under 20 words>", "confidential_flag": true | false, "confidential_reason": "<short phrase or null>"}
"""


def screen_note(raw_text: str) -> dict:
    response_text = gemini_client.generate(
        prompt=raw_text,
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        temperature=0,
    )
    result = json.loads(response_text)
    if result.get("decision") not in VALID_DECISIONS:
        raise ValueError(f"Screening returned invalid decision: {result.get('decision')!r}")
    return result


def run_screening() -> list[tuple[str, dict]]:
    """Screens every note currently in tracker status "New" and updates the
    tracker with the resulting status, reason, and confidentiality flag.
    """
    results = []
    for note_id in list(tracker.list_notes(status="New").keys()):
        note = load_raw_note(note_id)
        result = screen_note(note["raw_text"])
        status = DECISION_TO_STATUS[result["decision"]]
        tracker.set_status(note_id, status, reason=result["reason"])
        tracker.set_confidential_flag(
            note_id,
            flagged=result.get("confidential_flag", False),
            reason=result.get("confidential_reason"),
        )
        results.append((note_id, result))
    return results
