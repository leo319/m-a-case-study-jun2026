"""Stage 4 (backend) — apply the expert's analysis.

The expert *skill* (the agent) reads the verified research claims and produces a
memo spec containing (a) its own new inference claims and (b) the memo structure.
This backend ingests the new claims and re-runs the verifier, so the expert's
inferences are themselves checked: an inference that builds on a quarantined claim
is quarantined too (experts may only build on verified claims — PLAN.md §2).

CLI:
  python -m src.pipeline.expert --run RUNDIR --memo memo_spec.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..core import claims as claims_io
from ..hooks import verify_citations
from . import runspace


def apply_expert(run: runspace.Run, memo_spec: dict) -> dict:
    claims = claims_io.load_claims(run.ctx.claims_path)
    existing = {c["id"] for c in claims}
    for nc in memo_spec.get("new_claims", []):
        if nc["id"] in existing:
            continue
        nc.setdefault("status", "unverified")
        claims.append(nc)
    claims_io.save_claims(run.ctx.claims_path, claims)
    report = verify_citations.verify(run.ctx)
    runspace.set_stage_status(run, "expert", "awaiting_gate")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 4 backend: apply expert claims + verify.")
    ap.add_argument("--run", required=True)
    ap.add_argument("--memo", required=True)
    ap.add_argument("--cache", default=None)
    args = ap.parse_args()
    cache_dir = Path(args.cache) if args.cache else None
    run = runspace.open_run(args.run, cache_dir=cache_dir)
    memo_spec = json.loads(Path(args.memo).read_text(encoding="utf-8"))
    report = apply_expert(run, memo_spec)
    sc = report["status_counts"]
    print(f"expert: claims now {sc.get('verified',0)} verified, {sc.get('quarantined',0)} quarantined",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
