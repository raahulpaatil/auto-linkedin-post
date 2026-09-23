# Skinstinct Content Pipeline

Turns Meera's raw Telegram notes (text + voice) into review-ready LinkedIn
drafts in her voice. **No stage in this pipeline ever posts to LinkedIn.**
Every draft is delivered back to Meera via Telegram for manual review and
posting.

## Non-negotiables

1. Never auto-publish — every draft goes back to Meera for manual review.
2. Never invent a citation or statistic. If a note has no real, checkable
   source, the draft contains the literal placeholder
   `[CURRENT HOOK – Meera to add source]`.
3. Every draft is generated using [`voice/meera_voice_skill.md`](voice/meera_voice_skill.md)
   as the style contract — not optional background.
4. Notes that look like they contain confidential manufacturing detail or
   identifiable customer information are flagged, never silently dropped or
   silently drafted.

## Pipeline stages

| Stage    | File               | Status                                    |
|----------|--------------------|--------------------------------------------|
| Ingest   | `src/ingest.py`    | Working, in mock mode                      |
| Screen   | `src/screen.py`    | Not built yet (phase 2)                    |
| Draft    | `src/draft.py`     | Not built yet (phase 3)                    |
| Deliver  | `src/deliver.py`   | Not built yet (phase 4)                    |

`data/tracker.json` holds the status of every note (`New` / `Developing` /
`Parked` / `Discarded` / `Draft ready`), plus its confidentiality flag and,
once drafted, its draft text. `data/notes/` holds one JSON file per raw note.
Both are plain files meant to be committed to git — no database.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` starts in `PIPELINE_MODE=mock`, which needs no real credentials — it
reads fake incoming messages from `tests/sample_messages.json` and prints
outgoing messages to the terminal instead of calling Telegram.

## Running the phase 1 dry run

```bash
python3 main.py
```

This ingests the sample messages, writes one JSON file per note into
`data/notes/`, registers each in `data/tracker.json` with status `New`, and
prints the resulting tracker state. Re-running it is safe — re-ingesting the
same `message_id` just rewrites the same note file and leaves its tracker
entry as-is.

## What's still pending

- `voice/meera_voice_skill.md` — provided.
- `TELEGRAM_BOT_TOKEN` — pending, needed for phase 4 (live delivery).
- `GEMINI_API_KEY` — pending, needed for phase 2 (screening) and phase 3
  (drafting).
- GitHub repo name, visibility, and structure — to be confirmed before phase 5.
