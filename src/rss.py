"""Searches Google News RSS for real, checkable current sources on a note's
topic, before drafting. Extends non-negotiable rule 2's "use a real source if
one exists" beyond just what's already in the note — the drafting stage still
decides whether any result is genuinely relevant enough to cite (see
draft.py's guardrail instructions); this module only fetches candidates.

No API key needed — Google News RSS search is a public, unauthenticated feed.
"""

import xml.etree.ElementTree as ET

import requests

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


def search_google_news(
    query: str,
    max_results: int = 5,
    region: str = "IN",
    language: str = "en",
) -> list[dict]:
    """Returns up to max_results real articles as
    [{"title", "link", "published", "source"}, ...]. Returns [] on any
    network or parse failure — this is a best-effort research step, never a
    hard dependency for drafting to proceed.
    """
    params = {
        "q": query,
        "hl": f"{language}-{region}",
        "gl": region,
        "ceid": f"{region}:{language}",
    }
    try:
        response = requests.get(GOOGLE_NEWS_RSS_URL, params=params, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except (requests.RequestException, ET.ParseError):
        return []

    results = []
    for item in root.findall("./channel/item")[:max_results]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else None
        if title and link:
            results.append({"title": title, "link": link, "published": published, "source": source})
    return results
