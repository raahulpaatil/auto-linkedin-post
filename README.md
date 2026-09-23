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

| Stage    | File               | Status                          |
|----------|--------------------|----------------------------------|
| Ingest   | `src/ingest.py`    | Working — mock or live Telegram  |
| Screen   | `src/screen.py`    | Working, live Gemini calls       |
| Draft    | `src/draft.py`     | Working, live Gemini calls       |
| Deliver  | `src/deliver.py`   | Working — mock or live Telegram  |

`data/tracker.json` holds the status of every note (`New` / `Developing` /
`Parked` / `Discarded` / `Draft ready`), plus its confidentiality flag,
delivery flag, and, once drafted, its draft text. `data/notes/` holds one
JSON file per raw note. Both are plain files meant to be committed to git —
no database. `data/telegram_offset.json` (gitignored, machine-local) tracks
which real Telegram updates have already been ingested.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your real `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, and
`TELEGRAM_CHAT_ID` (the channel/chat the bot delivers drafts to — the bot
must already be an admin of that channel to post into it and to receive its
posts).

`PIPELINE_MODE` controls both ingest and deliver together:
- `mock` — ingest reads fake messages from `tests/sample_messages.json`;
  deliver prints to the terminal instead of calling Telegram. No real
  credentials needed for these two stages. Screening and drafting always
  call the real Gemini API regardless of this setting.
- `live` — ingest polls the real Telegram channel for new messages (text and
  voice, transcribed via Gemini); deliver sends real messages to
  `TELEGRAM_CHAT_ID`.

## Running the pipeline

```bash
python3 main.py
```

Runs ingest → screen → draft → deliver once, end to end, and prints a
tracker summary. Re-running is safe: ingest won't re-fetch what it's already
seen (same `message_id` in mock mode, or the persisted Telegram offset in
live mode), screen/draft only touch notes still in `New`/`Developing`, and
deliver only sends drafts not yet marked `delivered`.

Confidentiality-flagged notes are still drafted and delivered (the flag is
there so Meera reviews them with that context — rule 1's manual-review gate
is what actually keeps anything from reaching LinkedIn unreviewed), not
silently skipped.

## What's still pending

- `voice/meera_voice_skill.md` — provided, in use.
- `TELEGRAM_BOT_TOKEN` — provided, verified; live ingest and delivery both
  working (bot is admin of the target channel).
- `GEMINI_API_KEY` — provided, verified; in use for screening, drafting, and
  voice transcription.
- `TELEGRAM_CHAT_ID` — provided, verified via `getChat`/`getChatMember`.
- GitHub repo — done: [raahulpaatil/auto-linkedin-post](https://github.com/raahulpaatil/auto-linkedin-post) (private).

All four non-negotiables and all four pipeline stages are now live. What's
left is day-to-day use: running `main.py` whenever Meera wants her latest
notes processed (manually, or later on a schedule if she wants that
automated).
