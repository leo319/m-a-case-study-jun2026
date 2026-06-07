"""Single CLI entrypoint the CC-native skills call (so SKILL.md files stay thin and
the heavy logic stays in tool/). Uniform subcommands, no -m / cd gymnastics:

  python tool/scripts/cli.py map
  python tool/scripts/cli.py intake   --deal deal_spec/cintas_unifirst.yaml
  python tool/scripts/cli.py research --run RUNDIR --proposals proposals.json [--mock-sources map.json]
  python tool/scripts/cli.py expert   --run RUNDIR --memo memo_spec.json
  python tool/scripts/cli.py render   --run RUNDIR --memo memo_spec.json
  python tool/scripts/cli.py check-memo --run RUNDIR --memo memo_spec.json
  python tool/scripts/cli.py verify   --run RUNDIR
  python tool/scripts/cli.py validate --run RUNDIR
  python tool/scripts/cli.py gate     --run RUNDIR --stage research --presented "..." --steering "..." [--artifacts a,b]

Commands that produce a run path print it on the last stdout line.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from src.hooks import check_memo, validate_schema, verify_citations  # noqa: E402
from src.pipeline import expert, ingest_research, intake, render_memo, runspace  # noqa: E402


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cmd_map(_args) -> int:
    print(runspace.pipeline_map_markdown())
    return 0


def cmd_intake(args) -> int:
    run = intake.run_intake(args.deal)
    print(f"intake: {run.run_dir / 'intake.md'}", file=sys.stderr)
    print(str(run.run_dir))
    return 0


def cmd_research(args) -> int:
    run = runspace.open_run(args.run)
    proposals = _load(args.proposals)
    mock = _load(args.mock_sources) if args.mock_sources else None
    if mock:
        mock = {u: str((TOOL_ROOT / p)) for u, p in mock.items() if not u.startswith("_")}
    report = ingest_research.ingest(run, proposals, mock_sources=mock)
    sc = report["status_counts"]
    print(f"research: {sc.get('verified',0)} verified, {sc.get('quarantined',0)} quarantined", file=sys.stderr)
    print(str(run.run_dir / "research_brief.md"))
    return 0


def cmd_expert(args) -> int:
    run = runspace.open_run(args.run)
    report = expert.apply_expert(run, _load(args.memo))
    sc = report["status_counts"]
    print(f"expert: {sc.get('verified',0)} verified, {sc.get('quarantined',0)} quarantined", file=sys.stderr)
    return 0


def cmd_render(args) -> int:
    try:
        md = render_memo.render(args.run, _load(args.memo))
    except ValueError as e:
        print(f"render: REFUSED — {e}", file=sys.stderr)
        return 1
    out = Path(args.run) / "preliminary_memo.md"
    out.write_text(md, encoding="utf-8")
    print(str(out))
    return 0


def cmd_check_memo(args) -> int:
    problems = check_memo.check(args.run, _load(args.memo))
    if not problems:
        print("check_memo: OK")
        return 0
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


def cmd_verify(args) -> int:
    report = verify_citations.run(args.run)
    sc = report["status_counts"]
    print(f"verify: {sc.get('verified',0)} verified, {sc.get('quarantined',0)} quarantined")
    return 0


def cmd_validate(args) -> int:
    return validate_schema.run(args.run)


def cmd_gate(args) -> int:
    run = runspace.open_run(args.run)
    artifacts = args.artifacts.split(",") if args.artifacts else []
    runspace.record_gate(run, stage=args.stage, presented=args.presented,
                         steering=args.steering, artifacts=[a.strip() for a in artifacts if a.strip()])
    print(f"gate: recorded '{args.stage}' to {run.steering_log_path}", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="cli", description="Merger-analysis pipeline CLI.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("map").set_defaults(fn=cmd_map)

    p = sub.add_parser("intake"); p.add_argument("--deal", required=True); p.set_defaults(fn=cmd_intake)

    p = sub.add_parser("research"); p.add_argument("--run", required=True)
    p.add_argument("--proposals", required=True); p.add_argument("--mock-sources", default=None)
    p.set_defaults(fn=cmd_research)

    p = sub.add_parser("expert"); p.add_argument("--run", required=True); p.add_argument("--memo", required=True)
    p.set_defaults(fn=cmd_expert)

    p = sub.add_parser("render"); p.add_argument("--run", required=True); p.add_argument("--memo", required=True)
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("check-memo"); p.add_argument("--run", required=True); p.add_argument("--memo", required=True)
    p.set_defaults(fn=cmd_check_memo)

    p = sub.add_parser("verify"); p.add_argument("--run", required=True); p.set_defaults(fn=cmd_verify)
    p = sub.add_parser("validate"); p.add_argument("--run", required=True); p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("gate"); p.add_argument("--run", required=True); p.add_argument("--stage", required=True)
    p.add_argument("--presented", required=True); p.add_argument("--steering", required=True)
    p.add_argument("--artifacts", default=""); p.set_defaults(fn=cmd_gate)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
