"""Shared citation builder for the brief and memo renderers.

Goal: the reader can flip straight to the cited page. A 200-page prospectus must
NOT collapse into one opaque footnote. So citations are keyed by
*(source-document, locator)* and numbered ``<doc>.<page>`` — e.g. ``[3.1]``,
``[3.2]`` — and every entry names the section/page it points at. Documents are
identified by URL, so two source-ids pointing at the same filing share one
document number.

Markdown auto-footnotes (``[^1]``) are deliberately NOT used: most viewers
renumber them sequentially in the rendered output, which would erase the decimal
page scheme. Instead we emit literal bracket markers ``[3.1]`` plus a plain
``## Citations`` list — stable in any viewer, raw or rendered.

Used by both ``render_brief`` and ``render_memo`` so the citation style (and the
page-level granularity) is identical across the pipeline's deliverables.
"""
from __future__ import annotations


def _norm_url(u: str) -> str:
    return (u or "").strip().rstrip("/")


class CitationBuilder:
    """Stateful builder. Call :meth:`prescan` over every claim the document will
    cite (so single-locator documents stay ``[N]`` and multi-locator documents
    become ``[N.1]``, ``[N.2]`` …), then :meth:`cite` per claim while rendering,
    then :meth:`citations_md` / :meth:`sources_consulted_md` for the appendix."""

    def __init__(self, sources: dict[str, dict]):
        self.sources = sources
        self._doc_major: dict[str, int] = {}              # url -> major number
        self._doc_meta: dict[str, dict] = {}              # url -> {tier,title,url}
        self._loc_minor: dict[tuple[str, str], int] = {}  # (url, locator) -> minor
        self._doc_loc_count: dict[str, int] = {}          # url -> distinct locator count
        self._entries: dict[str, dict] = {}               # label -> entry

    def _src_for(self, claim: dict) -> dict | None:
        sid = (claim.get("source_ids") or [None])[0]
        if not sid:
            return None
        return self.sources.get(sid) or {"id": sid, "url": sid, "title": sid}

    def prescan(self, claims: list[dict]) -> None:
        """Count distinct locators per document so single-locator docs render as
        ``[N]`` and only genuinely multi-page docs get the ``[N.m]`` decimals."""
        seen: dict[str, set] = {}
        for c in claims:
            s = self._src_for(c)
            if not s:
                continue
            url = _norm_url(s.get("url", s.get("id", "")))
            loc = (c.get("locator") or "").strip()
            seen.setdefault(url, set()).add(loc)
        self._doc_loc_count = {u: len(v) for u, v in seen.items()}

    def cite(self, claim: dict) -> str:
        """Return the inline marker (e.g. ``[3.2]``) for a claim, or ``""`` for a
        sourceless (inference) claim. Registers the citation entry on first use."""
        s = self._src_for(claim)
        if not s:
            return ""
        url = _norm_url(s.get("url", s.get("id", "")))
        loc = (claim.get("locator") or "").strip()
        if url not in self._doc_major:
            self._doc_major[url] = len(self._doc_major) + 1
            self._doc_meta[url] = {
                "tier": s.get("tier", "?"),
                "title": s.get("title", url),
                "url": s.get("url", url),
            }
        major = self._doc_major[url]
        if self._doc_loc_count.get(url, 1) > 1:
            key = (url, loc)
            if key not in self._loc_minor:
                existing = [m for (u, _l), m in self._loc_minor.items() if u == url]
                self._loc_minor[key] = (max(existing) + 1) if existing else 1
            minor = self._loc_minor[key]
            label = f"{major}.{minor}"
        else:
            minor = 0
            label = f"{major}"
        if label not in self._entries:
            meta = self._doc_meta[url]
            self._entries[label] = {
                "major": major, "minor": minor, "tier": meta["tier"],
                "title": meta["title"], "locator": loc, "url": meta["url"],
            }
        return f"[{label}]"

    def citations_md(self) -> list[str]:
        """The ``## Citations`` block: one line per (document, page) actually cited,
        sorted by number, each naming the tier, title, locator and URL."""
        if not self._entries:
            return []
        rows = sorted(self._entries.values(), key=lambda e: (e["major"], e["minor"]))
        out = ["## Citations", ""]
        for e in rows:
            label = f"{e['major']}.{e['minor']}" if e["minor"] else f"{e['major']}"
            parts = [f"**[{label}]**", f"[{e['tier']}] {e['title']}"]
            if e["locator"]:
                parts.append(e["locator"])
            parts.append(e["url"])
            out.append("- " + " — ".join(parts))
        out.append("")
        return out

    def sources_consulted_md(self) -> list[str]:
        """The ``## Sources consulted (N)`` block: every distinct source document
        fetched and grounded for the deliverable (deduped by URL)."""
        by_url: dict[str, dict] = {}
        for s in self.sources.values():
            url = _norm_url(s.get("url", ""))
            if url and url not in by_url:
                by_url[url] = s
        rows = sorted(by_url.values(), key=lambda s: (s.get("tier", "Z"), s.get("title", "")))
        out = [f"## Sources consulted ({len(rows)})", "",
               "_Every distinct source document fetched and grounded for this brief. "
               "Tiers: T1 primary filings · T2 reputable press / advocacy filings · T3 secondary press._", ""]
        for s in rows:
            out.append(f"- [{s.get('tier','?')}] {s.get('title','?')} — {s.get('url','?')}")
        out.append("")
        return out
