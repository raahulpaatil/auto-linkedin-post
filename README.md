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

| Stage    | File               | Status                                      |
|----------|--------------------|----------------------------------------------|
| Ingest   | `src/ingest.py`    | Working, in mock mode (real Telegram pending) |
| Screen   | `src/screen.py`    | Working, live Gemini calls                    |
| Draft    | `src/draft.py`     | Working, live Gemini calls                    |
| Deliver  | `src/deliver.py`   | Not built yet (phase 4)                       |

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

`.env` starts in `PIPELINE_MODE=mock` for Telegram, which needs no real
credentials for ingest/deliver — it reads fake incoming messages from
`tests/sample_messages.json` and prints outgoing messages to the terminal
instead of calling Telegram. Screening always calls the real Gemini API, so
`GEMINI_API_KEY` in `.env` must be a real key.

## Running the pipeline

```bash
python3 main.py
```

This ingests the sample messages, writes one JSON file per note into
`data/notes/`, screens each new note with Gemini (Develop/Park/Discard, one-
line reason, confidentiality flag), drafts a full LinkedIn post for every
"Develop" note using `voice/meera_voice_skill.md` as the system prompt, and
updates `data/tracker.json` accordingly. Re-running it is safe — re-ingesting
the same `message_id` just rewrites the same note file, and only notes still
in status `New`/`Developing` get (re-)screened/(re-)drafted.

Confidentiality-flagged notes are still drafted (the flag is there so Meera
reviews them with that context — rule 1's manual-review gate is what actually
keeps anything from reaching LinkedIn unreviewed), not silently skipped.

## What's still pending

- `voice/meera_voice_skill.md` — provided.
- `TELEGRAM_BOT_TOKEN` — provided, verified against `getMe`; live polling/
  delivery still lands in phase 4.
- `GEMINI_API_KEY` — provided, verified and in use for screening and
  drafting (phases 2–3).
- GitHub repo — done: [raahulpaatil/auto-linkedin-post](https://github.com/raahulpaatil/auto-linkedin-post) (private).
