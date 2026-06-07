"""Deterministic citation verifier — the structural guardrail of the whole tool.

Every claim is set to verified or quarantined here, by code, not by a model. A
claim that cannot be grounded never reaches a memo.

Rules
-----
fact claims:
  * every cited source must exist in the registry          (else: dead/fabricated)
  * the source must be cached and pass an integrity check  (else: not fetched / tampered)
  * the verbatim quote must be present in the cached bytes  (else: quote not found)
  Mode is chosen per claim:
    - filing-locator : T1 filing + a `locator` present. (Milestone 1 does the same
      substring check and records the locator; section/figure-aware parsing is
      Milestone 3 — see PLAN.md §9.3. The mode tag is recorded now so nothing
      downstream has to change later.)
    - url-quote      : everything else (news / open-web citations).

inference claims:
  * may only build on status:verified claims. If any support is quarantined or
    missing -> quarantined. Resolved to a fixpoint so chains chain correctly;
    an unresolvable cycle is quarantined rather than left dangling.

Usage:
  python -m src.hooks.verify_citations --run runs/<deal>/<ts>
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ..core import cache
from ..core import claims as claims_io
from ..core import registry as registry_io
from ..core import textutil
from ..core.paths import RunContext, run_context


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _verify_fact(claim: dict, sources: dict[str, dict], cache_dir: Path) -> tuple[str, str, list[str]]:
    """Return (status, mode, reasons) for a fact claim."""
    reasons: list[str] = []
    source_ids = claim.get("source_ids", [])
    quote = claim.get("quote", "")

    # Pick mode from the first resolvable source (or default to url-quote).
    mode = "url-quote"
    for sid in source_ids:
        s = sources.get(sid)
        if s and s.get("tier") == "T1" and claim.get("locator"):
            mode = "filing-locator"
            break

    grounded = False
    for sid in source_ids:
        src = sources.get(sid)
        if src is None:
            reasons.append(f"source '{sid}' not in registry (dead or fabricated citation)")
            continue
        content_hash = src.get("content_hash")
        if not content_hash or not src.get("local_path"):
            reasons.append(f"source '{sid}' has no cached content (never fetched)")
            continue
        if not cache.verify_integrity(cache_dir, content_hash):
            reasons.append(f"source '{sid}' failed cache integrity check (missing or tampered)")
            continue
        content_text = textutil.to_text(cache.load(cache_dir, content_hash), src.get("media_type"))
        if textutil.quote_present(quote, content_text):
            grounded = True  # at least one cited source actually contains the quote
        else:
            reasons.append(f"quote not found in source '{sid}'")

    status = "verified" if (grounded and not reasons) else "quarantined"
    return status, mode, reasons


def verify(ctx: RunContext) -> dict:
    """Verify all claims in the run, write status back to claims.jsonl, and return a report."""
    claims = claims_io.load_claims(ctx.claims_path)
    sources = registry_io.load_registry(ctx.registry_path)
    by_id = claims_io.index_by_id(claims)
    checked_at = _now_iso()

    # Pass 1: fact claims (independent of each other).
    for c in claims:
        if c.get("type") != "fact":
            continue
        status, mode, reasons = _verify_fact(c, sources, ctx.cache_dir)
        c["status"] = status
        c["verification"] = {"checked_at": checked_at, "mode": mode, "reasons": reasons}

    # Pass 2: inference claims to a fixpoint (chains depend on chains).
    inferences = [c for c in claims if c.get("type") == "inference"]
    for c in inferences:
        c.setdefault("status", "unverified")
    changed = True
    while changed:
        changed = False
        for c in inferences:
            if c["status"] != "unverified":
                continue
            supports = c.get("supports", [])
            missing = [s for s in supports if s not in by_id]
            bad = [s for s in supports if s in by_id and by_id[s].get("status") == "quarantined"]
            if missing or bad:
                reasons = [f"support '{s}' does not exist" for s in missing]
                reasons += [f"built on quarantined claim '{s}'" for s in bad]
                c["status"] = "quarantined"
                c["verification"] = {"checked_at": checked_at, "mode": "inference-support", "reasons": reasons}
                changed = True
            elif all(by_id[s].get("status") == "verified" for s in supports):
                c["status"] = "verified"
                c["verification"] = {"checked_at": checked_at, "mode": "inference-support", "reasons": []}
                changed = True
    # Anything still unverified is stuck in a support cycle.
    for c in inferences:
        if c["status"] == "unverified":
            c["status"] = "quarantined"
            c["verification"] = {
                "checked_at": checked_at,
                "mode": "inference-support",
                "reasons": ["unresolved support cycle (no path to a verified base claim)"],
            }

    claims_io.save_claims(ctx.claims_path, claims)
    report = _build_report(claims, sources)
    _write_report(ctx, report)
    return report


def _build_report(claims: list[dict], sources: dict[str, dict]) -> dict:
    status_counts = Counter(c.get("status", "unverified") for c in claims)
    fact_claims = [c for c in claims if c.get("type") == "fact"]
    quarantined = [c for c in claims if c.get("status") == "quarantined"]

    # Tier distribution across cited sources of verified fact claims.
    tier_counts: Counter = Counter()
    for c in fact_claims:
        if c.get("status") != "verified":
            continue
        for sid in c.get("source_ids", []):
            s = sources.get(sid)
            if s:
                tier_counts[s.get("tier", "?")] += 1

    # Fabrication vs misattribution split (deterministic substring check only sees
    # fabrication/dead-source + quote-absent; semantic misattribution is the model
    # layer, added in Milestone 3).
    fabricated = sum(
        1 for c in quarantined
        for r in c.get("verification", {}).get("reasons", [])
        if "not in registry" in r or "never fetched" in r or "integrity" in r
    )
    quote_absent = sum(
        1 for c in quarantined
        for r in c.get("verification", {}).get("reasons", [])
        if "quote not found" in r
    )

    return {
        "total_claims": len(claims),
        "status_counts": dict(status_counts),
        "tier_distribution": dict(tier_counts),
        "fabricated_or_dead": fabricated,
        "quote_absent": quote_absent,
        "quarantined": [
            {
                "id": c["id"],
                "type": c.get("type"),
                "module": c.get("module"),
                "reasons": c.get("verification", {}).get("reasons", []),
            }
            for c in quarantined
        ],
    }


def _write_report(ctx: RunContext, report: dict) -> None:
    lines = ["# Verification report", ""]
    sc = report["status_counts"]
    lines.append(f"- Total claims: **{report['total_claims']}**")
    lines.append(f"- Verified: **{sc.get('verified', 0)}**  |  Quarantined: **{sc.get('quarantined', 0)}**  |  Unverified: **{sc.get('unverified', 0)}**")
    lines.append(f"- Fabricated / dead citations caught: **{report['fabricated_or_dead']}**")
    lines.append(f"- Quote-absent citations caught: **{report['quote_absent']}**")
    lines.append("")
    lines.append("## Tier distribution (verified fact claims)")
    if report["tier_distribution"]:
        for tier in ("T1", "T2", "T3", "T4"):
            if tier in report["tier_distribution"]:
                lines.append(f"- {tier}: {report['tier_distribution'][tier]}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Quarantined claims")
    if report["quarantined"]:
        for q in report["quarantined"]:
            lines.append(f"- `{q['id']}` ({q['type']}/{q['module']})")
            for r in q["reasons"]:
                lines.append(f"    - {r}")
    else:
        lines.append("- (none)")
    lines.append("")
    ctx.verification_report_path.write_text("\n".join(lines), encoding="utf-8")


def run(run_dir: str | Path, cache_dir: str | Path | None = None) -> dict:
    ctx = run_context(run_dir, cache_dir)
    return verify(ctx)


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic citation verifier.")
    ap.add_argument("--run", required=True, help="run directory")
    ap.add_argument("--cache", default=None, help="cache dir (defaults to shared /cache)")
    args = ap.parse_args()
    report = run(args.run, args.cache)
    sc = report["status_counts"]
    print(f"verify: {sc.get('verified', 0)} verified, {sc.get('quarantined', 0)} quarantined "
          f"({report['fabricated_or_dead']} fabricated/dead, {report['quote_absent']} quote-absent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
