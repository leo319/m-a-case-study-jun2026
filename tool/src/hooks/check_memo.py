"""Deterministic hook: a memo may only cite verified claims.

This is the guardrail at the very last boundary — the point where analysis becomes
the deliverable. If a memo spec references a claim that is quarantined, unverified,
or missing, this fails (exit 1). Combined with the citation verifier, it makes
"an ungrounded claim reaches the memo" structurally impossible, not merely unlikely.

Usage:
  python -m src.hooks.check_memo --run RUNDIR --memo memo_spec.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..core import claims as claims_io
from ..core.paths import claims_path


def check(run_dir: str | Path, memo_spec: dict) -> list[str]:
    claims = claims_io.load_claims(claims_path(run_dir))
    by_id = claims_io.index_by_id(claims)
    problems: list[str] = []
    for section in memo_spec.get("sections", []):
        for pt in section.get("points", []):
            cid = pt.get("claim_id")
            if cid is None:
                problems.append(f"section '{section.get('heading','?')}': a point has no claim_id")
                continue
            c = by_id.get(cid)
            if c is None:
                problems.append(f"'{cid}' cited in memo but absent from claims.jsonl")
            elif c.get("status") != "verified":
                problems.append(f"'{cid}' cited in memo but status is '{c.get('status')}', not verified")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="Check a memo cites only verified claims.")
    ap.add_argument("--run", required=True)
    ap.add_argument("--memo", required=True, help="memo spec JSON")
    args = ap.parse_args()
    memo_spec = json.loads(Path(args.memo).read_text(encoding="utf-8"))
    problems = check(args.run, memo_spec)
    if not problems:
        print("check_memo: OK — every cited claim is verified")
        return 0
    print(f"check_memo: FAILED — {len(problems)} problem(s):", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
