"""Coverage-map test (zero tokens).  Run: python tests/test_coverage.py

Builds a synthetic claims.jsonl spanning several checklist areas and checks the
searched/hits/gaps logic: covered areas counted, required/recommended areas with no
verified claim flagged as gaps, and claims tagged to unknown areas surfaced.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from src.core import claims as claims_io  # noqa: E402
from src.pipeline import coverage  # noqa: E402


def build_claims(d: Path):
    claims = [
        {"id": "c1", "statement": "rev", "type": "fact", "module": "research",
         "area": "target_fundamentals", "source_ids": ["s1"], "quote": "q", "status": "verified"},
        {"id": "c2", "statement": "antitrust", "type": "fact", "module": "tailrisk",
         "area": "antitrust_regulatory", "source_ids": ["s1"], "quote": "q", "status": "verified"},
        # litigation searched but nothing verified -> still a gap (recommended)
        {"id": "c3", "statement": "lit", "type": "fact", "module": "tailrisk",
         "area": "litigation_legal", "source_ids": ["s1"], "quote": "q", "status": "quarantined"},
        # a claim tagged to an area not in the checklist
        {"id": "c4", "statement": "weird", "type": "fact", "module": "research",
         "area": "made_up_area", "source_ids": ["s1"], "quote": "q", "status": "verified"},
    ]
    claims_io.save_claims(d / "claims.jsonl", claims)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    ok = True
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        build_claims(d)
        cmap = coverage.coverage_map(d)
        covered = {r["key"] for r in cmap["rows"] if r["hits"] > 0}
        gap_keys = {g["key"] for g in cmap["gaps"]}

        checks = [
            ("covered includes target_fundamentals + antitrust", covered >= {"target_fundamentals", "antitrust_regulatory"}),
            ("litigation_legal is a gap (searched, 0 verified)", "litigation_legal" in gap_keys),
            ("deal_rationale_synergies is a gap (required, not searched)", "deal_rationale_synergies" in gap_keys),
            ("covered areas NOT flagged as gaps", not (covered & gap_keys)),
            ("made_up_area surfaced as untracked", "made_up_area" in cmap["untracked"]),
            ("areas_covered == 2", cmap["areas_covered"] == 2),
        ]
        for name, passed in checks:
            print(f"  {'✅' if passed else '❌'} {name}")
            ok = ok and passed

    print(f"\n{'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
