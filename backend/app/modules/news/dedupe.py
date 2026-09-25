"""Remove obvious duplicates (syndicated/reposted copies) from one feed page.

Keys, in order: vendor id; normalized URL; normalized title on the same host. Articles on
different hosts are never merged on title alone, so unrelated stories with similar titles stay.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit

from app.modules.news.schemas import NewsArticle

_TRACKING_PARAMS = frozenset({"fbclid", "gclid"})
_NON_WORD_RE = re.compile(r"[^\w]+")


def _strip_www(host: str) -> str:
    return host[4:] if host.startswith("www.") else host


def normalize_url(url: str) -> str:
    """Scheme-less, lowercased host without `www.`, no fragment/tracking params/trailing slash."""
    parts = urlsplit(url.strip())
    host = _strip_www(parts.netloc.lower())
    query = urlencode(
        [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if not k.lower().startswith("utm_") and k.lower() not in _TRACKING_PARAMS
        ]
    )
    path = parts.path.rstrip("/")
    return f"{host}{path}" + (f"?{query}" if query else "")


def _title_key(article: NewsArticle) -> str | None:
    host = _strip_www((article.host or urlsplit(article.url).netloc).lower())
    title = _NON_WORD_RE.sub(" ", article.title.lower()).strip()
    return f"{host}|{title}" if host and title else None


def dedupe_articles(articles: list[NewsArticle]) -> list[NewsArticle]:
    """First occurrence wins; order is preserved."""
    seen: set[str] = set()
    kept: list[NewsArticle] = []
    for article in articles:
        keys = {f"id:{article.id}", f"url:{normalize_url(article.url)}"}
        title_key = _title_key(article)
        if title_key:
            keys.add(f"title:{title_key}")
        if keys & seen:
            continue
        seen |= keys
        kept.append(article)
    return kept
