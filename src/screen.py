"""Screen stage: score a raw note against 8 metrics, classify it as
Develop / Park / Discard, explain the bucket decision by referencing those
metrics, and set the confidentiality flag (non-negotiable rule 4 — flag
notes with manufacturing detail or identifiable customer info so they never
reach a public draft unreviewed).
"""

import json

from src import gemini_client, tracker
from src.constants import METRIC_KEYS
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
Telegram channel. You do not write any content — you only score, classify, \
and explain.

## Step 1: score these 8 metrics, each 1-5 (5 = strongest, except \
confidentiality_risk where 5 = highest risk)

- specificity: does the note contain a concrete fact, number, date, or \
  observed moment, rather than a vague idea?
- topic_fit: how well does it match one of Meera's recurring topics — \
  Ingredient Deep-Dive, Formulation Science, Founder Story, India-Specific \
  Context, Industry Transparency, Consumer Education, or Brand Philosophy?
- technical_depth: is there enough real formulation/scientific substance to \
  build a genuine mechanism section, not just a surface-level tip?
- voice_compatibility: can this become a post using Meera's actual \
  structure — concrete opening, stated intent, a concession, a mechanism, a \
  closing instruction — without forcing it?
- citability: does the note already contain, or would the topic benefit \
  from, a real checkable source (a named institution, a study, a figure)?
- completeness: is there enough raw material here for a full post, or is it \
  a one-line fragment that needs more before it's draftable?
- novelty: is this a specific, differentiated angle, or generic advice \
  already well covered elsewhere?
- confidentiality_risk: how much internal manufacturing detail or \
  identifiable customer information does the note contain? This scores \
  severity only — it does not by itself set confidential_flag (see Step 3).

## Step 2: classify

Decide exactly one:
- "Develop": enough concrete substance and topic fit to become a strong \
  LinkedIn post now.
- "Park": on-topic but too thin, vague, or unfinished to draft from yet — \
  it might become a post later with more detail.
- "Discard": personal, unrelated to Skinstinct/skincare, or has no usable \
  content angle (reminders, errands, unrelated chatter).

## Step 3: confidentiality (mandatory on every note, independent of Step 2)

Set confidential_flag to true if the note contains either of these, and \
only these:
- Specific internal manufacturing/formulation detail that goes beyond what \
  Meera would already say publicly (e.g. exact supplier names, unreleased \
  formulation ratios, internal batch/QC failure specifics).
- Identifiable customer information (a name, contact detail, address, or an \
  order/batch number tied to a specific named or otherwise identifiable \
  customer).

This check is mandatory on every note, completely independent of the \
decision — including notes you decide to "Discard". A note about an \
individual customer's order, complaint, or reaction is confidential even \
when it is not post-worthy content at all. Do not let "this isn't a content \
idea" cause you to skip the confidentiality check.

Example: a note reading "customer emailed her address, said she reacted to \
the serum, need her batch number" is decision "Discard" (it's a customer \
service task, not a content idea) AND confidential_flag true \
(confidential_reason: "identifiable customer contact and reaction detail").

A note can also be both "Develop" and confidential — that means the \
underlying topic is worth a post, but the specific sensitive detail must be \
stripped or reviewed by Meera before drafting. Set confidential_reason to a \
short phrase naming what triggered the flag, or null if confidential_flag is \
false.

## Step 4: explain the bucket

Write bucket_explanation: 2-4 sentences that explicitly reference at least \
two of the 8 metric scores by name and number to justify the decision — \
don't just restate the decision. For example: "topic_fit scored 5/5 as a \
clean Consumer Education angle, and specificity scored 4/5 on the concrete \
mechanism described, which together made this a Develop even though \
citability was only 2/5."

## Step 5: search query (Develop only)

If decision is "Develop", write search_query: a short 5-8 word Google News \
search query capturing this note's specific topic, to help find a real, \
current source before drafting. If decision is not "Develop", set \
search_query to null.

Never invent facts not present in the note. Base every field only on the \
note text given to you.

Respond with strict JSON only, no markdown fencing, matching exactly:
{"metrics": {"specificity": 1-5, "topic_fit": 1-5, "technical_depth": 1-5, "voice_compatibility": 1-5, "citability": 1-5, "completeness": 1-5, "novelty": 1-5, "confidentiality_risk": 1-5}, "decision": "Develop" | "Park" | "Discard", "reason": "<one sentence, under 20 words>", "bucket_explanation": "<2-4 sentences referencing at least two metrics by name and score>", "confidential_flag": true | false, "confidential_reason": "<short phrase or null>", "search_query": "<string, or null if not Develop>"}
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
    metrics = result.get("metrics", {})
    missing = [k for k in METRIC_KEYS if k not in metrics]
    if missing:
        raise ValueError(f"Screening response missing metrics: {missing}")
    return result


def run_screening() -> list[tuple[str, dict]]:
    """Screens every note currently in tracker status "New" and writes the
    full screening result (status, reason, metrics, bucket explanation,
    confidentiality flag, search query) to the tracker in one save.
    """
    results = []
    for note_id in list(tracker.list_notes(status="New").keys()):
        note = load_raw_note(note_id)
        result = screen_note(note["raw_text"])
        status = DECISION_TO_STATUS[result["decision"]]
        tracker.set_screening_result(
            note_id,
            status=status,
            reason=result["reason"],
            bucket_explanation=result["bucket_explanation"],
            metrics=result["metrics"],
            confidential_flag=result.get("confidential_flag", False),
            confidential_reason=result.get("confidential_reason"),
            search_query=result.get("search_query"),
        )
        results.append((note_id, result))
    return results
