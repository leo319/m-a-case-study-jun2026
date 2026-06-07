"""Milestone 2 proof (MOCK) — the full thin-slice loop, end to end, ZERO tokens.

No network, no model. Fixtures stand in for what the research and expert agents
would produce; the real Python spine does everything deterministic. It proves the
machine works before we spend a cent on a live run:

  intake  ->  ingest research (fetch=mock) -> verify  ->  expert (+verify)
          ->  render memo (fail-closed)     ->  audit log

and shows that, on realistically-shaped agent output, the verifier still
quarantines a hallucinated number, a dead citation, and an inference built on a lie.

Run:
  python scripts/run_milestone2_mock.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from src.core import claims as claims_io  # noqa: E402
from src.core.paths import RUNS_ROOT  # noqa: E402
from src.pipeline import expert, ingest_research, intake, render_memo, runspace  # noqa: E402

FIX = TOOL_ROOT / "tests" / "fixtures" / "m2"
DEAL_SPEC = TOOL_ROOT / "deal_spec" / "cintas_unifirst.yaml"
TS = "_mock_m2"

EXPECTED = {
    "c0001": "verified",     # grounded fact (revenue)
    "c0002": "verified",     # grounded fact (margin)
    "c0003": "verified",     # grounded fact (organic growth)
    "c0004": "quarantined",  # hallucinated number — quote absent
    "c0005": "quarantined",  # dead/fabricated citation
    "c0006": "verified",     # grounded fact (retention, news source)
    "c0007": "verified",     # inference on verified facts
    "c0008": "quarantined",  # inference built on the hallucinated claim
    "e0001": "verified",     # expert inference on verified claims
}


def resolve_mock_sources() -> dict:
    raw = json.loads((FIX / "mock_sources.json").read_text(encoding="utf-8"))
    return {url: str(TOOL_ROOT / rel) for url, rel in raw.items() if not url.startswith("_")}


def main() -> int:
    print("=" * 72)
    print("MILESTONE 2 PROOF (MOCK) — full thin-slice loop, no tokens")
    print("=" * 72)

    # clean prior mock run
    run_dir = RUNS_ROOT / "cintas_unifirst" / TS
    if run_dir.exists():
        shutil.rmtree(run_dir)

    # --- Stage 1: intake ---
    run = intake.run_intake(DEAL_SPEC, cache_dir=run_dir / "cache", ts=TS)
    print(f"\n[1] intake        -> {run.ctx.audit('intake.md').relative_to(TOOL_ROOT)}")
    runspace.record_gate(run, stage="intake",
                         presented="Deal skeleton + steering for Cintas/UniFirst.",
                         steering="Approved. Focus the slice on target fundamentals.",
                         artifacts=["intake.md"])

    # --- Stage 3: research (mock fetch) ---
    proposals = json.loads((FIX / "research_proposals.json").read_text(encoding="utf-8"))
    report = ingest_research.ingest(run, proposals, mock_sources=resolve_mock_sources())
    sc = report["status_counts"]
    print(f"[3] research      -> {run.ctx.artifact('research_findings.md').relative_to(TOOL_ROOT)}  "
          f"({sc.get('verified',0)} verified, {sc.get('quarantined',0)} quarantined)")
    runspace.record_gate(run, stage="research",
                         presented=f"{sc.get('verified',0)} verified, {sc.get('quarantined',0)} quarantined "
                                   f"({report['fabricated_or_dead']} dead/fabricated, {report['quote_absent']} quote-absent).",
                         steering="Continue. Note the margin compression in the memo.",
                         artifacts=["research_findings.md", "verification_report.md"])

    # --- Stage 4: expert (+verify) ---
    memo_spec = json.loads((FIX / "expert_memo_spec.json").read_text(encoding="utf-8"))
    expert.apply_expert(run, memo_spec)
    print("[4] expert        -> applied expert inference(s) + re-verified")

    # --- render memo (fail-closed) ---
    memo_md = render_memo.render(run.run_dir, memo_spec)
    run.ctx.artifact("preliminary_memo.md").write_text(memo_md, encoding="utf-8")
    print(f"    render        -> {run.ctx.artifact('preliminary_memo.md').relative_to(TOOL_ROOT)}")
    runspace.record_gate(run, stage="expert",
                         presented="Preliminary memo on target fundamentals (verified claims only).",
                         steering="(awaiting analyst review)",
                         artifacts=["preliminary_memo.md"])

    # ---- checks ----
    print("\n[verify] claim statuses:\n")
    claims = claims_io.load_claims(run.ctx.claims_path)
    by_id = claims_io.index_by_id(claims)
    all_ok = True
    for cid, exp in EXPECTED.items():
        actual = by_id[cid]["status"] if cid in by_id else "MISSING"
        ok = actual == exp
        all_ok = all_ok and ok
        print(f"    {cid:6} expected {exp:12} actual {actual:12} {'✅' if ok else '❌'}")

    # guard: a memo citing a quarantined claim must be REFUSED
    print("\n[guard] memo citing a quarantined claim (c0004) must be refused:")
    bad_spec = {"title": "bad", "sections": [{"heading": "x", "points": [{"claim_id": "c0004"}]}]}
    try:
        render_memo.render(run.run_dir, bad_spec)
        print("    ❌ render did NOT refuse a quarantined citation")
        guard_ok = False
    except ValueError:
        print("    ✅ render refused (fail-closed) — ungrounded claim cannot reach the memo")
        guard_ok = True

    print("\n[audit] steering log written:",
          (run.steering_log_path.relative_to(TOOL_ROOT)))

    print("\n" + "=" * 72)
    if all_ok and guard_ok:
        print("RESULT: ✅ PASS — full loop works; fabrications quarantined; memo grounded.")
    else:
        print("RESULT: ❌ FAIL — see mismatches above.")
    print("=" * 72)

    print("\n----- preliminary_memo.md -----\n")
    print(memo_md)
    return 0 if (all_ok and guard_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
