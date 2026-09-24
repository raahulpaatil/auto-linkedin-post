# Skinstinct Content Pipeline

Turns Meera's raw Telegram notes (text + voice) into review-ready LinkedIn
drafts in her voice. **No stage in this pipeline ever posts to LinkedIn.**
Every draft is delivered back to Meera via Telegram for manual review and
posting.

Two ways to run it:
- **Locally** (`main.py`) — a script you run whenever you want, polling
  Telegram once and processing whatever's new. Good for testing.
- **Deployed** (Vercel, `api/telegram_webhook.py`) — always-on. Telegram
  pushes each new note to a webhook the instant it's posted, and the pipeline
  processes it within seconds. This is the "live" setup.

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
| Ingest   | `src/ingest.py`    | Working — mock, local-poll, or webhook |
| Screen   | `src/screen.py`    | Working, live Gemini calls       |
| Draft    | `src/draft.py`     | Working, live Gemini calls       |
| Deliver  | `src/deliver.py`   | Working — mock or live Telegram  |

`data/tracker.json` holds the status of every note (`New` / `Developing` /
`Parked` / `Discarded` / `Draft ready`), plus its confidentiality flag,
delivery flag, and, once drafted, its draft text. `data/notes/` holds one
JSON file per raw note. Both are read/written through `src/storage.py`,
which supports two backends (see below) — not a database.

## Storage backends

- `STORAGE_BACKEND=local` (default) — reads/writes `data/` on local disk.
  Used by `main.py` for local dev.
- `STORAGE_BACKEND=github` — reads/writes the same files inside this GitHub
  repo via the Contents API instead, since the deployed webhook has no
  persistent local filesystem between invocations. Every write is a real git
  commit, so the repo's history doubles as an audit log of every note's
  status changes. Known limitation: no locking, so two near-simultaneous
  webhook calls could race and lose an update — a non-issue at solo,
  low-volume note traffic.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your real `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, and
`TELEGRAM_CHAT_ID` (the bot must already be an admin of that channel).
`PIPELINE_MODE=mock` (default) needs no real Telegram credentials for
ingest/deliver — it reads `tests/sample_messages.json` and prints instead of
sending. `PIPELINE_MODE=live` polls/sends for real. Screening and drafting
always call the real Gemini API regardless of this setting.

```bash
python3 main.py
```

Runs ingest → screen → draft → deliver once and prints a tracker summary.
Re-running is safe: ingest won't re-fetch what it's already seen, screen/
draft only touch notes still in `New`/`Developing`, and deliver only sends
drafts not yet marked `delivered`.

## Deploying to Vercel (the live setup)

1. **Import the repo.** On [vercel.com/new](https://vercel.com/new), import
   [raahulpaatil/auto-linkedin-post](https://github.com/raahulpaatil/auto-linkedin-post).
   No framework preset needed — Vercel auto-detects `api/*.py` as Python
   serverless functions.
2. **Set environment variables** in the Vercel project's Settings →
   Environment Variables:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
   - `TELEGRAM_CHAT_ID`
   - `GITHUB_TOKEN` — a fine-grained PAT scoped to this repo with Contents:
     Read and write (can reuse the same one used to set up the repo, or a
     fresh one — either way, treat it as a secret, only in Vercel's env vars,
     never in a file that gets committed)
   - `GITHUB_REPO` = `raahulpaatil/auto-linkedin-post`
   - `STORAGE_BACKEND` = `github`
   - `PIPELINE_MODE` = `live`
3. **Deploy.** Vercel builds and gives you a production URL, e.g.
   `https://auto-linkedin-post.vercel.app`.
4. **Register the Telegram webhook** — send me that URL and I'll point
   Telegram at `https://<your-url>/api/telegram_webhook` via one `setWebhook`
   call (needs only the bot token, which I already have). This is a one-time
   step; Telegram remembers it.
5. **Test it** — post a note in the channel and watch for the draft to come
   back within a few seconds.

Once live, the webhook handles everything automatically: no need to run
`main.py` at all unless you want a manual local test pass.

### Notes on the Vercel deployment

- `vercel.json` sets `maxDuration: 60` on the webhook function — screening +
  drafting are two sequential Gemini calls, plus a voice download/transcribe
  step for voice notes, so the default short timeout isn't enough. If your
  Vercel plan doesn't allow 60s functions, lower this and expect voice notes
  in particular to be at risk of timing out — flag it if that happens and
  we'll adjust (e.g. split transcription into a separate step).
- On any error mid-pipeline, the webhook still returns `200 ok` to Telegram
  rather than letting it retry — retrying could reprocess a note that
  already partially succeeded (e.g. drafted but not yet delivered). This
  means a failure is only visible in the Vercel function logs, not retried
  automatically.

## Confidentiality handling

Confidentiality-flagged notes are still drafted and delivered (the flag is
there so Meera reviews them with that context — rule 1's manual-review gate
is what actually keeps anything from reaching LinkedIn unreviewed), not
silently skipped.

## What's pending

- Vercel deployment — code is ready and tested; needs Meera to import the
  repo and set env vars (steps above), then send the resulting URL so the
  Telegram webhook can be registered.

Everything else — all four non-negotiables, all four pipeline stages, both
storage backends — is built, verified, and pushed.
