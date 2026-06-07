"""Render a narrative research brief from a brief spec — fail-closed.

PLAN.md §3 wants the brief to read like a human briefing — exec summary → company &
industry descriptions → findings by area — and be *fully cited*. This renders that
from agent-authored prose carrying inline `[[claim_id]]` citation tokens:

  * every referenced claim must be `status: verified` (else it refuses to render),
  * each token expands to a numbered footnote pointing at the claim's source.

So the analyst gets readable narrative, and every factual citation still traces to a
verified, machine-checked source. Prose that makes a load-bearing factual assertion
should carry a token; general framing can be uncited, but anything specific must cite.

brief_spec:
  {"title", "subtitle"?, "sections": [{"heading", "body"}]}     body = markdown prose w/ [[c01]] tokens

CLI:
  python tool/scripts/cli.py render-brief --run RUNDIR --brief brief_spec.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ..core import claims as claims_io
from ..core import registry as registry_io

_TOKEN = re.compile(r"\[\[([A-Za-z0-9_]+)\]\]")


def referenced_ids(brief_spec: dict) -> list[str]:
    ids: list[str] = []
    for sec in brief_spec.get("sections", []):
        ids += _TOKEN.findall(sec.get("body", ""))
    return ids


def check(run_dir: str | Path, brief_spec: dict) -> list[str]:
    claims = claims_io.load_claims(Path(run_dir) / "claims.jsonl")
    by_id = claims_io.index_by_id(claims)
    problems: list[str] = []
    for cid in referenced_ids(brief_spec):
        c = by_id.get(cid)
        if c is None:
            problems.append(f"[[{cid}]] cited in brief but absent from claims.jsonl")
        elif c.get("status") != "verified":
            problems.append(f"[[{cid}]] cited in brief but status is '{c.get('status')}', not verified")
    return problems


def render(run_dir: str | Path, brief_spec: dict) -> str:
    run_dir = Path(run_dir)
    problems = check(run_dir, brief_spec)
    if problems:
        raise ValueError("brief cites non-verified claims:\n  - " + "\n  - ".join(problems))

    by_id = claims_io.index_by_id(claims_io.load_claims(run_dir / "claims.jsonl"))
    sources = registry_io.load_registry(run_dir / "source_registry.json")
    footnotes: list[str] = []
    fn_for_source: dict[str, int] = {}

    def cite(cid: str) -> str:
        c = by_id[cid]
        sid = (c.get("source_ids") or [None])[0]
        if not sid:  # inference claim — no direct source; cite nothing inline
            return ""
        if sid not in fn_for_source:
            s = sources.get(sid, {})
            fn_for_source[sid] = len(footnotes) + 1
            footnotes.append(f"[^{fn_for_source[sid]}]: [{s.get('tier','?')}] {s.get('title','?')} — {s.get('url','?')}")
        return f"[^{fn_for_source[sid]}]"

    lines = [f"# {brief_spec.get('title', 'Research brief')}", ""]
    if brief_spec.get("subtitle"):
        lines += [f"_{brief_spec['subtitle']}_", ""]
    for sec in brief_spec.get("sections", []):
        lines += [f"## {sec['heading']}", ""]
        body = _TOKEN.sub(lambda m: cite(m.group(1)), sec.get("body", ""))
        # collapse consecutive duplicate footnote markers (e.g. two claims, same source)
        body = re.sub(r"(\[\^\d+\])\1+", r"\1", body)
        lines.append(body.strip())
        lines.append("")
    if footnotes:
        lines += ["---", ""] + footnotes + [""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render narrative research brief (fail-closed).")
    ap.add_argument("--run", required=True)
    ap.add_argument("--brief", required=True)
    args = ap.parse_args()
    brief_spec = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    try:
        md = render(args.run, brief_spec)
    except ValueError as e:
        print(f"render-brief: REFUSED — {e}", file=sys.stderr)
        return 1
    out = Path(args.run) / "research_brief.md"
    out.write_text(md, encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
