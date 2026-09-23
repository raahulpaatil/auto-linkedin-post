"""Thin wrapper around the Gemini API. screen.py and draft.py call generate(),
not the SDK directly, so the model, auth, and JSON-mode handling live in one
place.
"""

import os

from google import genai
from google.genai import types

GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
# Alias, not a pinned version — tracks whichever flash model Google currently
# recommends, so this doesn't need updating every time a model is retired.
DEFAULT_MODEL = "gemini-flash-latest"

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get(GEMINI_API_KEY_ENV, "")
    if not api_key or api_key.startswith("REPLACE_ME"):
        raise RuntimeError(
            f"{GEMINI_API_KEY_ENV} is not set. Add a real Gemini API key to .env "
            "before calling gemini_client.generate()."
        )
    _client = genai.Client(api_key=api_key)
    return _client


def generate(
    prompt: str,
    system_instruction: str | None = None,
    response_mime_type: str | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float | None = None,
) -> str:
    """Calls Gemini with the given prompt and optional system instruction.
    Pass response_mime_type="application/json" to request strict JSON output.
    """
    client = _get_client()
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type=response_mime_type,
        temperature=temperature,
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    return response.text


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    """Transcribes a voice note's audio bytes to text via Gemini.

    Not yet wired — pending real Telegram audio download (phase 4).
    """
    _get_client()
    raise NotImplementedError("Real audio transcription lands in phase 4.")
