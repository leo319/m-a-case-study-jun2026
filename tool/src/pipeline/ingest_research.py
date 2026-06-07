"""Stage 3 (backend) — turn the research agent's proposed claims into grounded,
verified claims.

The research *skill* (the agent) does the searching and proposes claims as JSON:
each fact carries a source {url, tier, title} + a verbatim quote; inferences carry
`supports`. This backend does the deterministic part the model must not be trusted
with:

  1. fetch each cited URL into the content-addressed cache (real) — or read a local
     fixture (mock mode, for zero-token testing),
  2. register the sources, assemble claims.jsonl,
  3. run the citation verifier (already built) to mark each claim verified/quarantined,
  4. write research_brief.md (verified findings) alongside verification_report.md.

A URL that won't fetch is registered without content so the verifier quarantines
any claim citing it — a dead/fabricated citation can't slip through.

Proposals JSON:
  {"area": "...", "proposals": [
     {"claim_id","statement","type":"fact","module":"research",
      "source":{"id","title","url","tier"},"quote","locator"?},
     {"claim_id","statement","type":"inference","module":"research","supports":[...]}
  ]}

CLI:
  python -m src.pipeline.ingest_research --run RUNDIR --proposals proposals.json [--mock-sources map.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..core import cache, fetch
from ..core import claims as claims_io
from ..core import registry as registry_io
from ..hooks import verify_citations
from . import runspace


def _guess_media_type(path: Path) -> str:
    suf = path.suffix.lower()
    if suf in (".html", ".htm"):
        return "text/html"
    if suf == ".json":
        return "application/json"
    return "text/plain"


def _fetch_source(src: dict, cache_dir: Path, mock_sources: dict | None) -> dict:
    """Return a registry source dict. On any failure, return one with no content
    (content_hash absent) so the verifier quarantines claims citing it."""
    sid = src["id"]
    url = src["url"]
    base = {"id": sid, "title": src.get("title", url), "url": url, "tier": src.get("tier", "T4")}
    try:
        if mock_sources is not None:
            if url not in mock_sources:
                raise FileNotFoundError(f"mock: no fixture for {url} (simulated dead link)")
            fpath = Path(mock_sources[url])
            data = fpath.read_bytes()
            content_hash, local_path = cache.store(cache_dir, data)
            base.update({
                "retrieved_at": "1970-01-01T00:00:00+00:00",  # fixed for reproducible mock
                "content_hash": content_hash,
                "local_path": local_path,
                "media_type": _guess_media_type(fpath),
            })
            return base
        fetched = fetch.fetch_url(url, cache_dir, source_id=sid, tier=base["tier"], title=base["title"])
        return fetched
    except Exception as e:  # noqa: BLE001 — any fetch failure => uncacheable source
        base["fetch_error"] = str(e)
        return base


def ingest(run: runspace.Run, proposals: dict, mock_sources: dict | None = None) -> dict:
    cache_dir = run.ctx.cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    # 1. Collect unique sources from fact proposals and fetch/cache them.
    sources: dict[str, dict] = registry_io.load_registry(run.ctx.registry_path)
    seen_urls: dict[str, str] = {}  # url -> source_id, to dedupe
    for p in proposals.get("proposals", []):
        src = p.get("source")
        if not src:
            continue
        if src["url"] in seen_urls:
            continue
        seen_urls[src["url"]] = src["id"]
        sources[src["id"]] = _fetch_source(src, cache_dir, mock_sources)
    registry_io.save_registry(run.ctx.registry_path, sources)

    # 2. Assemble claims (embed source object -> source_ids reference).
    claims = claims_io.load_claims(run.ctx.claims_path)
    existing_ids = {c["id"] for c in claims}
    for p in proposals.get("proposals", []):
        cid = p["claim_id"]
        if cid in existing_ids:
            continue
        claim = {
            "id": cid,
            "statement": p["statement"],
            "type": p["type"],
            "module": p.get("module", "research"),
            "status": "unverified",
        }
        if p["type"] == "fact":
            claim["source_ids"] = [p["source"]["id"]]
            claim["quote"] = p.get("quote", "")
            if p.get("locator"):
                claim["locator"] = p["locator"]
        else:
            claim["supports"] = p.get("supports", [])
        if "confidence" in p:
            claim["confidence"] = p["confidence"]
        claims.append(claim)
    claims_io.save_claims(run.ctx.claims_path, claims)

    # 3. Verify (writes statuses + verification_report.md).
    report = verify_citations.verify(run.ctx)

    # 4. Research brief from verified claims.
    _write_research_brief(run, proposals.get("area", "research"), report)
    runspace.set_stage_status(run, "research", "awaiting_gate")
    return report


def _write_research_brief(run: runspace.Run, area: str, report: dict) -> None:
    claims = claims_io.load_claims(run.ctx.claims_path)
    sources = registry_io.load_registry(run.ctx.registry_path)
    verified = [c for c in claims if c.get("status") == "verified"]
    facts = [c for c in verified if c.get("type") == "fact"]
    infers = [c for c in verified if c.get("type") == "inference"]

    lines = [f"# Research findings (verified claims) — {area}", "",
             "_Structured appendix: the verified claims the narrative `research_brief.md` is "
             "built from. Quarantined claims are in `verification_report.md` and never reach the memo._", ""]
    lines.append("## Verified findings (facts)")
    if facts:
        for c in facts:
            sid = (c.get("source_ids") or ["?"])[0]
            s = sources.get(sid, {})
            lines.append(f"- {c['statement']}")
            lines.append(f"    - source [{s.get('tier','?')}]: {s.get('title','?')} — {s.get('url','?')}")
            lines.append(f"    - quote: \"{c.get('quote','').strip()}\"")
    else:
        lines.append("- (none verified)")
    lines += ["", "## Verified inferences"]
    if infers:
        for c in infers:
            lines.append(f"- {c['statement']}  _(builds on {', '.join(c.get('supports', []))})_")
    else:
        lines.append("- (none)")
    sc = report["status_counts"]
    lines += ["", "## Coverage / verification summary",
              f"- Verified: {sc.get('verified',0)}  |  Quarantined: {sc.get('quarantined',0)}",
              f"- Fabricated/dead caught: {report['fabricated_or_dead']}  |  Quote-absent caught: {report['quote_absent']}",
              ""]
    (run.run_dir / "research_findings.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 3 backend: ingest + verify research proposals.")
    ap.add_argument("--run", required=True)
    ap.add_argument("--proposals", required=True, help="proposals JSON from the research agent")
    ap.add_argument("--mock-sources", default=None, help="JSON map url->fixture path (offline mode)")
    ap.add_argument("--cache", default=None)
    args = ap.parse_args()

    cache_dir = Path(args.cache) if args.cache else None
    run = runspace.open_run(args.run, cache_dir=cache_dir)
    proposals = json.loads(Path(args.proposals).read_text(encoding="utf-8"))
    mock = json.loads(Path(args.mock_sources).read_text(encoding="utf-8")) if args.mock_sources else None
    report = ingest(run, proposals, mock_sources=mock)
    sc = report["status_counts"]
    print(f"research: {sc.get('verified',0)} verified, {sc.get('quarantined',0)} quarantined "
          f"-> {run.run_dir / 'research_findings.md'}", file=sys.stderr)
    print(str(run.run_dir / "research_findings.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
