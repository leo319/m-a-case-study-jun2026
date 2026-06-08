"""Stage 2 — Source Planning (backend).

Before research fans out, the tool proposes a source list *by class* so the analyst
can approve / add / remove / edit it at a gate (PLAN.md §3, stage 2). The deterministic
part is the deal-agnostic list of source CLASSES to consider — so blind spots are
visible. The agent fills in concrete, deal-specific sources with a one-line rationale.

The plan is **deal-wide**: every planned source carries its coverage `area`, so the
Stage-2 gate shows the analyst everything research will pull, grouped by area. A source
surfaced by the planner's open discovery sweep (beyond the canonical checklist) is
tagged `via: "scout"` so the gate can call out what discovery added.

A planned source:
  {id, title, area, class, tier, url?|search_hint?, rationale, via?}

CLI:
  python tool/scripts/cli.py source-plan-template          # baseline classes (for the agent)
  python tool/scripts/cli.py source-plan --run R --plan plan.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import coverage, runspace

# Deal-agnostic source classes to consider for ANY deal. Lives in the tool, not the
# deal_spec — that's what makes coverage gaps visible rather than silent.
SOURCE_CLASSES = [
    {"class": "filings", "default_tier": "T1", "desc": "SEC filings: 10-K, 10-Q, 8-K, merger proxy / 424B3 / S-4"},
    {"class": "regulators", "default_tier": "T1", "desc": "Antitrust (DOJ/FTC) and sector regulators"},
    {"class": "court_dockets", "default_tier": "T1", "desc": "Litigation dockets / legal proceedings"},
    {"class": "news_analyst", "default_tier": "T2", "desc": "Major news and sell-side analyst research"},
    {"class": "trade_press", "default_tier": "T3", "desc": "Industry / specialist trade press"},
    {"class": "activist_short", "default_tier": "T4", "desc": "Short-seller and activist reports"},
]
_CLASS_ORDER = [c["class"] for c in SOURCE_CLASSES]


def baseline_template() -> dict:
    return {"source_classes": SOURCE_CLASSES}


def apply_plan(run: runspace.Run, plan: dict) -> dict:
    run.ctx.audit("source_plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    run.ctx.artifact("source_plan.md").write_text(_render(plan), encoding="utf-8")
    runspace.set_stage_status(run, "source_plan", "awaiting_gate")
    return plan


def _area_order() -> tuple[list[str], dict[str, str]]:
    """Coverage-checklist key order + key->title, so the plan reads as one system with
    the coverage map. Degrades gracefully if the checklist can't be loaded."""
    try:
        checklist = coverage.load_checklist()
        return [a["key"] for a in checklist], {a["key"]: a.get("title", a["key"]) for a in checklist}
    except Exception:  # noqa: BLE001 — checklist is a nicety here, not a hard dep
        return [], {}


def _render(plan: dict) -> str:
    deal = plan.get("deal_id") or plan.get("area") or "(deal)"
    lines = [f"# Source plan — {deal}", "",
             "_Proposed sources to research, grouped by area then class. Approve / add / "
             "remove / edit before research fans out. `(via scout)` = surfaced by open "
             "discovery, beyond the canonical checklist._", ""]

    # Group by area (deal-wide). Sources with no area fall under one (unassigned) heading
    # so old single-area plans still render.
    by_area: dict[str, list] = {}
    for s in plan.get("planned_sources", []):
        by_area.setdefault(s.get("area") or "(unassigned)", []).append(s)

    order, titles = _area_order()
    known = [k for k in order if k in by_area]
    extra = sorted(k for k in by_area if k not in order and k != "(unassigned)")
    tail = ["(unassigned)"] if "(unassigned)" in by_area else []
    for area in known + extra + tail:
        lines += [f"## {titles.get(area, area)}", ""]
        by_class: dict[str, list] = {}
        for s in by_area[area]:
            by_class.setdefault(s.get("class", "(unclassified)"), []).append(s)
        for cls in _CLASS_ORDER + [k for k in by_class if k not in _CLASS_ORDER]:
            if cls not in by_class:
                continue
            lines.append(f"### {cls}")
            for s in by_class[cls]:
                target = s.get("url") or (f"search: {s['search_hint']}" if s.get("search_hint") else "(to be located)")
                via = " _(via scout)_" if s.get("via") else ""
                lines.append(f"- [{s.get('tier', '?')}] **{s.get('title', '?')}**{via} — {target}")
                if s.get("rationale"):
                    lines.append(f"    - {s['rationale']}")
            lines.append("")

    skipped = plan.get("classes_skipped") or []
    lines += ["## Classes intentionally skipped", ""]
    if skipped:
        for sk in skipped:
            lines.append(f"- **{sk.get('class', '?')}** — {sk.get('reason', '')}")
    else:
        lines.append("- (none — all considered classes have at least one planned source)")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 2 source planning.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("template").set_defaults(fn=lambda a: print(json.dumps(baseline_template(), indent=2)) or 0)
    p = sub.add_parser("apply")
    p.add_argument("--run", required=True)
    p.add_argument("--plan", required=True)
    args = ap.parse_args()
    if args.cmd == "template":
        print(json.dumps(baseline_template(), indent=2))
        return 0
    run = runspace.open_run(args.run)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    apply_plan(run, plan)
    print(str(run.ctx.artifact("source_plan.md")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
