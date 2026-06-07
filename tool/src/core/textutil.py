"""Text normalisation used by the quote check.

A verbatim quote and the source it came from rarely match byte-for-byte once HTML
reflow and whitespace differences are involved. We normalise both sides the same
way before comparing: strip tags (for HTML) and collapse runs of whitespace.

Deliberately conservative — case and punctuation are preserved, so a quote still
has to be genuinely present, not merely similar.
"""
from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)


def html_to_text(raw: str) -> str:
    raw = _SCRIPT_STYLE_RE.sub(" ", raw)
    raw = _TAG_RE.sub(" ", raw)
    return html.unescape(raw)


def normalize(text: str) -> str:
    """Collapse whitespace; trim. Case/punctuation preserved."""
    return _WS_RE.sub(" ", text).strip()


def to_text(raw_bytes: bytes, media_type: str | None) -> str:
    text = raw_bytes.decode("utf-8", errors="replace")
    if media_type and "html" in media_type.lower():
        text = html_to_text(text)
    return text


def quote_present(quote: str, content_text: str) -> bool:
    return normalize(quote) in normalize(content_text)
