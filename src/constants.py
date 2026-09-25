"""Shared constants with no dependencies on other src modules — kept
separate specifically to avoid import cycles (ingest <-> deliver <-> screen
all need at least one of these).
"""

METRIC_KEYS = [
    "specificity",
    "topic_fit",
    "technical_depth",
    "voice_compatibility",
    "citability",
    "completeness",
    "novelty",
    "confidentiality_risk",
]

# Every message this pipeline posts starts with one of these. Both get
# delivered into the same channel notes come from, so the bot's own posts
# arrive back as channel_post updates — these prefixes let ingest_message()
# recognise and skip its own messages instead of re-ingesting them as new
# notes (see src/ingest.py and api/telegram_webhook.py).
SCREENING_MESSAGE_PREFIX = "Screened:"
DELIVERY_MESSAGE_PREFIX = "Draft ready:"
BOT_MESSAGE_PREFIXES = (SCREENING_MESSAGE_PREFIX, DELIVERY_MESSAGE_PREFIX)
