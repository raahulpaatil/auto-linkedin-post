"""Voice-note transcription, isolated from ingest.py so the mock/live switch
lives in one place.
"""

import os

from src import gemini_client


def transcribe_voice(file_id: str, mock_transcript: str | None = None) -> str:
    mode = os.environ.get("PIPELINE_MODE", "mock")
    if mode == "mock":
        if mock_transcript is None:
            raise ValueError(
                f"No 'transcript_placeholder' provided for voice file {file_id!r} "
                "in mock mode."
            )
        return mock_transcript

    from src.telegram_client import RealTelegramClient

    audio_bytes = RealTelegramClient().download_voice_file(file_id)
    return gemini_client.transcribe_audio(audio_bytes)
