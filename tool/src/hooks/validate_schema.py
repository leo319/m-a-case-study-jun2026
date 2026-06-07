"""Deterministic hook: validate every claim and source against the JSON schemas.

Exit code 0 == all valid; 1 == at least one malformed object. Runs before the
verifier so the verifier can assume well-formed input.

Usage:
  python -m src.hooks.validate_schema --run runs/<deal>/<ts>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..core import claims as claims_io
from ..core import registry as registry_io
from ..core import schema
from ..core.paths import run_context


def run(run_dir: str | Path) -> int:
    ctx = run_context(run_dir)
    claims = claims_io.load_claims(ctx.claims_path)
    sources = registry_io.load_registry(ctx.registry_path)
    problems = schema.validate_all(claims, sources)

    if not problems:
        print(f"schema: OK — {len(claims)} claims, {len(sources)} sources valid")
        return 0

    print(f"schema: FAILED — {len(problems)} invalid object(s):", file=sys.stderr)
    for obj_id, errs in problems.items():
        print(f"  {obj_id}", file=sys.stderr)
        for e in errs:
            print(f"    - {e}", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate claims/sources against JSON schemas.")
    ap.add_argument("--run", required=True, help="run directory containing claims.jsonl + source_registry.json")
    args = ap.parse_args()
    return run(args.run)


if __name__ == "__main__":
    raise SystemExit(main())
