"""Stage 1 — Intake & Scoping (backend).

Parses a deal_spec yaml, creates a run, and writes the scoping artifact the
orchestrator presents at Gate 1. In the thin M2 slice the deal skeleton comes
straight from the analyst-provided spec (seeds, not yet grounded) — research is
where seeds become verified claims.

CLI:
  python -m src.pipeline.intake --deal deal_spec/cintas_unifirst.yaml [--cache DIR]
prints the new run directory on the last line (the orchestrator captures it).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from . import runspace


def run_intake(deal_spec_path: str | Path, *, cache_dir: Path | None = None,
               ts: str | None = None) -> runspace.Run:
    spec = yaml.safe_load(Path(deal_spec_path).read_text(encoding="utf-8"))
    deal = spec.get("deal", {})
    deal_id = deal.get("id") or Path(deal_spec_path).stem
    run = runspace.create_run(deal_id, cache_dir=cache_dir, ts=ts)

    # `or` not the default arg: a key present with a null value returns None,
    # which would break the renderers. Coerce null -> empty.
    intake = {
        "deal": deal,
        "seed_docs": spec.get("seed_docs") or [],
        "seed_terms": spec.get("seed_terms") or {},
        "run_config": spec.get("run_config") or {},
    }
    run.ctx.audit("intake.json").write_text(json.dumps(intake, indent=2) + "\n", encoding="utf-8")
    run.ctx.audit("intake.md").write_text(_render_intake_md(intake), encoding="utf-8")
    runspace.set_stage_status(run, "intake", "awaiting_gate")
    return run


def _render_intake_md(intake: dict) -> str:
    d = intake["deal"]
    acq, tgt = d.get("acquirer", {}), d.get("target", {})
    rc = intake["run_config"]
    steering = rc.get("steering") or {}
    lines = [
        "# Intake & Scoping",
        "",
        "## Deal skeleton (analyst-provided seeds — not yet grounded)",
        f"- **Acquirer:** {acq.get('name','?')} ({acq.get('ticker','?')} / {acq.get('exchange','?')})",
        f"- **Target:** {tgt.get('name','?')} ({tgt.get('ticker','?')} / {tgt.get('exchange','?')})",
        f"- **Announcement date:** {d.get('announcement_date') or '_(none — confirm signed/proposed/hypothetical)_'}",
    ]
    if d.get("status_note"):
        lines.append(f"- **Status note:** {d['status_note'].strip()}")
    lines += ["", "## Seed documents to fetch first"]
    for s in intake["seed_docs"]:
        lines.append(f"- [{s.get('tier','?')}] {s.get('title','?')} — {s.get('url','?')}")
    lines += ["", "## Run config"]
    lines.append(f"- **Depth:** {rc.get('depth','?')}")
    lines.append(f"- **Emphasize areas:** {', '.join(rc.get('emphasize_areas') or []) or '(none)'}")
    notes = steering.get("notes")
    if notes:
        # notes may be a YAML string (folded `>` / literal `|`) or a list; normalize to
        # a list of non-empty lines so a string isn't iterated character-by-character.
        notes = [ln.strip() for ln in notes.splitlines() if ln.strip()] if isinstance(notes, str) else list(notes)
        lines += ["", "## Analyst steering — notes"]
        lines += [f"- {n}" for n in notes]
    priorities = steering.get("priorities")
    if priorities:
        priorities = [ln.strip() for ln in priorities.splitlines() if ln.strip()] if isinstance(priorities, str) else list(priorities)
        lines += ["", "## Analyst steering — priorities"]
        lines += [f"- {p}" for p in priorities]
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 1 intake: parse deal_spec, create a run.")
    ap.add_argument("--deal", required=True, help="path to deal_spec yaml")
    ap.add_argument("--cache", default=None, help="cache dir (defaults to shared /cache)")
    args = ap.parse_args()
    cache = Path(args.cache) if args.cache else None
    run = run_intake(args.deal, cache_dir=cache)
    print(f"intake: wrote {run.ctx.audit('intake.md')}", file=sys.stderr)
    # last line = run dir, for the orchestrator to capture
    print(str(run.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
