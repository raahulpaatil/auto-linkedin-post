"""Thin wrapper around the Gemini API. Stubbed until GEMINI_API_KEY is real —
screen.py and draft.py call generate(), not the SDK directly, so swapping in
the real key later needs no changes to the pipeline stages.
"""

import os

GEMINI_API_KEY_ENV = "GEMINI_API_KEY"


def _ensure_configured() -> None:
    api_key = os.environ.get(GEMINI_API_KEY_ENV, "")
    if not api_key or api_key.startswith("REPLACE_ME"):
        raise RuntimeError(
            f"{GEMINI_API_KEY_ENV} is not set. Add a real Gemini API key to .env "
            "before calling gemini_client.generate()."
        )
    import google.generativeai as genai

    genai.configure(api_key=api_key)


def generate(prompt: str, system_instruction: str | None = None) -> str:
    """Calls Gemini with the given prompt and optional system instruction.

    Not yet wired to a live call — screen.py (phase 2) and draft.py (phase 3)
    will fill this in once GEMINI_API_KEY is provided.
    """
    _ensure_configured()
    raise NotImplementedError(
        "Gemini call wiring lands in phase 2 (screening) and phase 3 (drafting)."
    )


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    """Transcribes a voice note's audio bytes to text via Gemini.

    Not yet wired — pending GEMINI_API_KEY and real Telegram audio download.
    """
    _ensure_configured()
    raise NotImplementedError("Real audio transcription lands in phase 4.")
