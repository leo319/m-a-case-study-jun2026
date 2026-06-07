"""Fetch a URL into the content-addressed cache and return a registry source.

Used by the real intake/research stages. The milestone-1 demo does NOT use this
(it seeds the cache from a local fixture so the proof needs no network), but this
is the path a live run takes. Stdlib urllib only — no third-party HTTP dependency.

SEC EDGAR enforces a fair-access policy: the User-Agent MUST identify a real
contact, in the format "Company Name AdminContact@domain". A generic browser UA is
rejected (HTTP 403). Override with FETCH_USER_AGENT if needed.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from . import cache

# SEC-compliant format: "<name> <admin contact email>". Not a browser UA.
DEFAULT_UA = os.environ.get(
    "FETCH_USER_AGENT",
    "Merger Analysis Tool (Nicholas Kang) nicholas.kang.jun.jie@gmail.com",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_url(
    url: str,
    cache_dir: Path,
    *,
    source_id: str,
    tier: str,
    title: str | None = None,
    timeout: int = 30,
) -> dict:
    """Fetch url, cache the bytes, and return a source dict ready for the registry.

    Raises urllib errors on network/HTTP failure — callers decide whether a fetch
    failure means 'quarantine any claim citing this source'.
    """
    req = Request(url, headers={"User-Agent": DEFAULT_UA, "Accept": "*/*"})
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted, analyst-supplied)
        data = resp.read()
        media_type = resp.headers.get_content_type()

    content_hash, local_path = cache.store(cache_dir, data)
    return {
        "id": source_id,
        "title": title or url,
        "url": url,
        "tier": tier,
        "retrieved_at": _now_iso(),
        "content_hash": content_hash,
        "local_path": local_path,
        "media_type": media_type,
    }
