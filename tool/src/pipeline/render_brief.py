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
from ..core.citations import CitationBuilder
from ..core.paths import claims_path, out_path, registry_path

_TOKEN = re.compile(r"\[\[([A-Za-z0-9_]+)\]\]")
# collapse consecutive identical citation markers, e.g. [3.1][3.1] -> [3.1]
_DUP_MARKER = re.compile(r"(\[\d+(?:\.\d+)?\])\1+")


def _tidy(body: str) -> str:
    """Remove the whitespace artifacts a removed inference marker leaves behind —
    e.g. a space before sentence punctuation or before a closing ``_`` (which would
    otherwise break markdown emphasis). Leaves table rows untouched.

    Also rewrites a bare ``~`` used as "approximately" (``~$5.5B``, ``~103%``) to
    ``c. `` (circa): a lone tilde is the GFM strikethrough delimiter, so two of them on
    one line render everything between as struck-through text."""
    out = []
    for line in body.split("\n"):
        line = re.sub(r"~(?=[\d$])", "c. ", line)  # ~ as "approximately"/circa (incl. tables)
        if "|" not in line:  # don't disturb markdown tables
            line = re.sub(r"[ \t]+([.,;:)_])", r"\1", line)      # space before punctuation
            line = re.sub(r"(\S)[ \t]{2,}(\S)", r"\1 \2", line)  # collapse internal runs
            line = re.sub(r"[ \t]+$", "", line)                   # trailing space
        out.append(line)
    return "\n".join(out)


def referenced_ids(brief_spec: dict) -> list[str]:
    ids: list[str] = []
    for sec in brief_spec.get("sections", []):
        ids += _TOKEN.findall(sec.get("body", ""))
    return ids


def check(run_dir: str | Path, brief_spec: dict) -> list[str]:
    claims = claims_io.load_claims(claims_path(run_dir))
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

    by_id = claims_io.index_by_id(claims_io.load_claims(claims_path(run_dir)))
    sources = registry_io.load_registry(registry_path(run_dir))

    # Pre-scan referenced claims so single-locator sources stay [N] and only
    # genuinely multi-page sources get the decimal [N.m] page markers.
    builder = CitationBuilder(sources)
    builder.prescan([by_id[cid] for cid in referenced_ids(brief_spec) if cid in by_id])

    def cite(cid: str) -> str:
        c = by_id.get(cid)
        return builder.cite(c) if c else ""

    lines = [f"# {brief_spec.get('title', 'Research brief')}", ""]
    if brief_spec.get("subtitle"):
        lines += [f"_{brief_spec['subtitle']}_", ""]
    for sec in brief_spec.get("sections", []):
        lines += [f"## {sec['heading']}", ""]
        body = _TOKEN.sub(lambda m: cite(m.group(1)), sec.get("body", ""))
        body = _DUP_MARKER.sub(r"\1", body)  # collapse [3.1][3.1] -> [3.1]
        body = _tidy(body)                   # clean whitespace left by removed inference markers
        lines.append(body.strip())
        lines.append("")
    citations = builder.citations_md()
    if citations:
        lines += ["---", ""] + citations
    lines += builder.sources_consulted_md()
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
    out = out_path(args.run, "research_brief.md")
    out.write_text(md, encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
