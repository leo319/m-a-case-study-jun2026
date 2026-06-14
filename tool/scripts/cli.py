"""Single CLI entrypoint the CC-native skills call (so SKILL.md files stay thin and
the heavy logic stays in tool/). Uniform subcommands, no -m / cd gymnastics:

  python tool/scripts/cli.py map
  python tool/scripts/cli.py intake   --deal deal_spec/cintas_unifirst.yaml
  python tool/scripts/cli.py research --run RUNDIR --proposals proposals.json [--mock-sources map.json]
  python tool/scripts/cli.py expert   --run RUNDIR --memo memo_spec.json
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
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from src.core import cache, fetch, textutil  # noqa: E402
from src.core.paths import CACHE_ROOT, RUNS_ROOT, audit_dir, out_path  # noqa: E402
from src.eval import eval_run  # noqa: E402
from src.hooks import check_memo, validate_schema, verify_citations  # noqa: E402
from src.pipeline import (  # noqa: E402
    coverage, expert, ingest_research, intake, render_brief, runspace, source_plan,
)


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
    print(str(run.ctx.artifact("research_findings.md")))
    return 0


def cmd_expert(args) -> int:
    run = runspace.open_run(args.run)
    memo_spec = _load(args.memo)
    report = expert.apply_expert(run, memo_spec)
    sc = report["status_counts"]
    print(f"expert: {sc.get('verified',0)} verified, {sc.get('quarantined',0)} quarantined", file=sys.stderr)
    for line in coverage.utilization_report(coverage.utilization(args.run, memo_spec)):
        print(line, file=sys.stderr)
    return 0


def cmd_render_brief(args) -> int:
    try:
        md = render_brief.render(args.run, _load(args.brief))
    except ValueError as e:
        print(f"render-brief: REFUSED — {e}", file=sys.stderr)
        return 1
    out = out_path(args.run, "research_brief.md")
    out.write_text(md, encoding="utf-8")
    print(str(out))
    return 0


def cmd_render_doc(args) -> int:
    """Render any narrative doc spec (title/sections/[[id]] prose) fail-closed to --out."""
    try:
        md = render_brief.render(args.run, _load(args.spec))
    except ValueError as e:
        print(f"render-doc: REFUSED — {e}", file=sys.stderr)
        return 1
    out = out_path(args.run, args.out)
    out.write_text(md, encoding="utf-8")
    print(str(out))
    return 0


def cmd_check_memo(args) -> int:
    memo_spec = _load(args.memo)
    for w in check_memo.lint(memo_spec):  # non-fatal structural warnings
        print(f"  ⚠ {w}", file=sys.stderr)
    problems = check_memo.check(args.run, memo_spec)
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


def cmd_source_plan_template(_args) -> int:
    print(json.dumps(source_plan.baseline_template(), indent=2))
    return 0


def cmd_source_plan(args) -> int:
    run = runspace.open_run(args.run)
    plan = _load(args.plan)
    source_plan.apply_plan(run, plan)
    print(f"source-plan: wrote {run.ctx.artifact('source_plan.md')}", file=sys.stderr)
    print(str(run.ctx.artifact("source_plan.md")))
    return 0


def cmd_coverage_checklist(_args) -> int:
    for a in coverage.load_checklist():
        print(f"{a['key']:26} [{','.join(a.get('lens', []))}] {a.get('default','')} — {a.get('title','')}")
        subs = a.get("subtopics") or []
        if subs:
            print(f"{'':26} subtopics (each must be addressed or flagged): {', '.join(subs)}")
        canon = a.get("canonical_sources") or []
        if canon:
            print(f"{'':26} canonical sources to propose: {'; '.join(canon)}")
    return 0


def cmd_coverage(args) -> int:
    cmap = coverage.run(args.run)
    print(f"coverage: {cmap['areas_covered']}/{cmap['total_areas']} areas covered, "
          f"{len(cmap['gaps'])} gaps -> {audit_dir(args.run) / 'coverage_report.md'}")
    return 0


def cmd_inspect(args) -> int:
    """Fetch a URL via the SEC-compliant fetch path and surface readable text.

    The agent's read tool when WebFetch is blocked (e.g. SEC 403). With --grep,
    prints normalized sentences containing any '|'-separated term — copy these
    verbatim as claim quotes (the verifier extracts text the same way, so a span
    copied from here is guaranteed to match)."""
    import re
    src = fetch.fetch_url(args.url, CACHE_ROOT, source_id="_inspect", tier="T1", title=args.url)
    text = textutil.normalize(textutil.to_text(cache.load(CACHE_ROOT, src["content_hash"]), src["media_type"]))
    print(f"# fetched {len(text)} chars (text) from {args.url}", file=sys.stderr)
    if args.grep:
        terms = [t for t in args.grep.split("|") if t]
        sents = re.split(r"(?<=[.%])\s+(?=[A-Z(0-9$])", text)
        n = 0
        for s in sents:
            s = s.strip()
            if 30 < len(s) < args.maxlen and any(t.lower() in s.lower() for t in terms):
                print(s + "\n")
                n += 1
                if n >= args.max:
                    break
        if n == 0:
            print("(no matching sentences)")
    else:
        print(text[: args.max_chars])
    return 0


def cmd_eval_plan(args) -> int:
    manifest = eval_run.plan(args.run, chunk_size=args.chunk_size)
    print(f"eval-plan: {manifest['total_surfaced']} surfaced claims "
          f"({manifest['facts']} facts, {manifest['inferences']} inferences) -> "
          f"{manifest['n_chunks']} chunk(s) in {eval_run.chunks_dir(args.run)}", file=sys.stderr)
    print(str(eval_run.eval_dir(args.run) / "manifest.json"))
    return 0


def cmd_eval_source(args) -> int:
    print(eval_run.source_dossier(args.run, args.claim, full=args.full))
    return 0


def cmd_eval_aggregate(args) -> int:
    sc = eval_run.aggregate(args.run)
    print(f"eval-aggregate: precision {eval_run._pct(sc['fact_precision'])} "
          f"({sc['facts_pass']}/{sc['facts_total']}), "
          f"fabrication {eval_run._pct(sc['fabrication_rate'])}, "
          f"misattribution {eval_run._pct(sc['misattribution_rate'])}, "
          f"inference-validity {eval_run._pct(sc['inference_validity_rate'])}", file=sys.stderr)
    print(str(eval_run.eval_dir(args.run) / "scorecard.md"))
    return 0


def cmd_eval_dashboard(args) -> int:
    out = eval_run.dashboard(args.runs_root)
    print(f"eval-dashboard: wrote {out}", file=sys.stderr)
    print(str(out))
    return 0


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

    p = sub.add_parser("render-brief"); p.add_argument("--run", required=True); p.add_argument("--brief", required=True)
    p.set_defaults(fn=cmd_render_brief)

    p = sub.add_parser("render-doc"); p.add_argument("--run", required=True); p.add_argument("--spec", required=True)
    p.add_argument("--out", required=True, help="output filename within the run dir")
    p.set_defaults(fn=cmd_render_doc)

    p = sub.add_parser("check-memo"); p.add_argument("--run", required=True); p.add_argument("--memo", required=True)
    p.set_defaults(fn=cmd_check_memo)

    p = sub.add_parser("verify"); p.add_argument("--run", required=True); p.set_defaults(fn=cmd_verify)
    p = sub.add_parser("validate"); p.add_argument("--run", required=True); p.set_defaults(fn=cmd_validate)

    sub.add_parser("coverage-checklist").set_defaults(fn=cmd_coverage_checklist)
    p = sub.add_parser("coverage"); p.add_argument("--run", required=True); p.set_defaults(fn=cmd_coverage)

    sub.add_parser("source-plan-template").set_defaults(fn=cmd_source_plan_template)
    p = sub.add_parser("source-plan"); p.add_argument("--run", required=True); p.add_argument("--plan", required=True)
    p.set_defaults(fn=cmd_source_plan)

    p = sub.add_parser("inspect"); p.add_argument("--url", required=True)
    p.add_argument("--grep", default=None, help="'|'-separated terms; prints matching sentences")
    p.add_argument("--max", type=int, default=15); p.add_argument("--maxlen", type=int, default=320)
    p.add_argument("--max-chars", type=int, default=4000, dest="max_chars")
    p.set_defaults(fn=cmd_inspect)

    p = sub.add_parser("eval-plan"); p.add_argument("--run", required=True)
    p.add_argument("--chunk-size", type=int, default=10, dest="chunk_size")
    p.set_defaults(fn=cmd_eval_plan)

    p = sub.add_parser("eval-source"); p.add_argument("--run", required=True)
    p.add_argument("--claim", required=True); p.add_argument("--full", action="store_true")
    p.set_defaults(fn=cmd_eval_source)

    p = sub.add_parser("eval-aggregate"); p.add_argument("--run", required=True)
    p.set_defaults(fn=cmd_eval_aggregate)

    p = sub.add_parser("eval-dashboard")
    p.add_argument("--runs-root", default=str(RUNS_ROOT), dest="runs_root")
    p.set_defaults(fn=cmd_eval_dashboard)

    p = sub.add_parser("gate"); p.add_argument("--run", required=True); p.add_argument("--stage", required=True)
    p.add_argument("--presented", required=True); p.add_argument("--steering", required=True)
    p.add_argument("--artifacts", default=""); p.set_defaults(fn=cmd_gate)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
