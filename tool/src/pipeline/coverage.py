"""Coverage map — the §1 "Comprehensiveness" mechanism.

Reads the deal-agnostic coverage checklist and the run's claims, then reports, per
area: was it searched, how many verified claims it has, and — crucially — which
required/recommended areas are still blind spots. Makes gaps visible instead of
silent.

CLI:
  python tool/scripts/cli.py coverage-checklist     # print the deal-agnostic areas
  python tool/scripts/cli.py coverage --run RUNDIR  # write coverage_report.md
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import yaml

from ..core import claims as claims_io
from ..core.paths import CONFIG_DIR, audit_dir, claims_path

CHECKLIST_PATH = CONFIG_DIR / "coverage_checklist.yaml"


def load_checklist() -> list[dict]:
    data = yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))
    return data.get("areas", [])


def coverage_map(run_dir: str | Path) -> dict:
    areas = load_checklist()
    claims = claims_io.load_claims(claims_path(run_dir))
    verified = Counter()
    attempted = Counter()
    for c in claims:
        a = c.get("area")
        if not a:
            continue
        attempted[a] += 1
        if c.get("status") == "verified":
            verified[a] += 1

    known = {a["key"] for a in areas}
    rows, gaps = [], []
    for a in areas:
        k = a["key"]
        hits = verified.get(k, 0)
        if hits > 0:
            status = "covered"
        elif attempted.get(k, 0) > 0:
            status = "attempted (nothing verified)"
        else:
            status = "not searched"
        rows.append({**a, "hits": hits, "status": status})
        if hits == 0 and a.get("default") in ("required", "recommended"):
            gaps.append({"key": k, "title": a["title"], "default": a["default"], "status": status})

    untracked = sorted(set(attempted) - known)
    return {
        "rows": rows,
        "gaps": gaps,
        "untracked": untracked,
        "areas_covered": sum(1 for r in rows if r["hits"] > 0),
        "total_areas": len(areas),
    }


def write_report(run_dir: str | Path, cmap: dict) -> Path:
    lines = [
        "# Coverage map", "",
        f"- Areas covered: **{cmap['areas_covered']}/{cmap['total_areas']}**",
        f"- Open gaps (required/recommended areas with no verified claims): **{len(cmap['gaps'])}**", "",
        "| Area | Lens | Default | Status | Verified claims |",
        "|---|---|---|---|---|",
    ]
    for r in cmap["rows"]:
        lens = ", ".join(r.get("lens", []))
        lines.append(f"| {r['title']} | {lens} | {r.get('default','')} | {r['status']} | {r['hits']} |")
    lines += ["", "## Gaps (blind spots to close)", ""]
    if cmap["gaps"]:
        for g in cmap["gaps"]:
            lines.append(f"- **{g['title']}** ({g['default']}) — {g['status']}")
    else:
        lines.append("- (none — every required/recommended area has verified coverage)")
    if cmap["untracked"]:
        lines += ["", "## Claims tagged to areas not in the checklist", ""]
        lines += [f"- `{u}`" for u in cmap["untracked"]]
    lines.append("")
    out = audit_dir(run_dir) / "coverage_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def run(run_dir: str | Path) -> dict:
    cmap = coverage_map(run_dir)
    write_report(run_dir, cmap)
    return cmap


def main() -> int:
    ap = argparse.ArgumentParser(description="Coverage map (searched/hits/gaps).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("checklist")
    p = sub.add_parser("map")
    p.add_argument("--run", required=True)
    args = ap.parse_args()
    if args.cmd == "checklist":
        for a in load_checklist():
            print(f"{a['key']:26} [{','.join(a.get('lens', []))}] {a.get('default','')}")
        return 0
    cmap = run(args.run)
    print(f"coverage: {cmap['areas_covered']}/{cmap['total_areas']} areas covered, {len(cmap['gaps'])} gaps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
