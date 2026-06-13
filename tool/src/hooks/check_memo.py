"""Deterministic hook: a memo may only cite verified claims.

This is the guardrail at the very last boundary — the point where analysis becomes
the deliverable. If a memo spec references a claim that is quarantined, unverified,
or missing, this fails (exit 1). Combined with the citation verifier, it makes
"an ungrounded claim reaches the memo" structurally impossible, not merely unlikely.

The narrative memo spec carries citations as inline ``[[claim_id]]`` tokens inside
each section's ``body`` (the same shape ``render_brief`` renders). An older spec shape
used per-section ``points`` with a ``claim_id`` each; both are handled so the guard keeps
biting whichever shape it's handed.

Beyond the hard fail, this also emits **non-fatal structural lint** warnings (mirroring
``coverage``'s depth check — a nudge at the gate, not a gate): inference-stacking (a wall
of consecutive "Our view" blockquotes) and smuggled figures (a declarative sentence with a
``$``/``%``/digit that sits outside a blockquote and carries no citation token).

Usage:
  python -m src.hooks.check_memo --run RUNDIR --memo memo_spec.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ..core import claims as claims_io
from ..core.paths import claims_path

# Mirror render_brief's token + the citation-stripping it does, so the lint sees prose
# the way the rendered memo will read.
_TOKEN = re.compile(r"\[\[([A-Za-z0-9_]+)\]\]")
# A declarative sentence smuggling a number: contains a digit, $, or % once tokens are
# stripped. We only care about figures that look load-bearing, not list ordinals etc.
_HAS_FIGURE = re.compile(r"[\$%]|\d")


def _section_cited_ids(section: dict) -> list[str]:
    """Claim ids a section cites — from ``body`` tokens (narrative spec) and/or from
    legacy ``points[].claim_id`` (older spec). Either shape, or both, is accepted."""
    ids = _TOKEN.findall(section.get("body", "") or "")
    for pt in section.get("points", []) or []:
        cid = pt.get("claim_id")
        if cid is not None:
            ids.append(cid)
    return ids


def _has_legacy_points_without_claim_id(section: dict) -> bool:
    return any(pt.get("claim_id") is None for pt in (section.get("points") or []))


def check(run_dir: str | Path, memo_spec: dict) -> list[str]:
    """Hard problems (exit-1): a cited claim is missing or not verified.

    Mirrors ``render_brief.check`` — scan each section's ``body`` for ``[[id]]`` tokens
    (and any legacy ``points``) and flag a cited claim that is absent from claims.jsonl
    or whose status is not ``verified``."""
    claims = claims_io.load_claims(claims_path(run_dir))
    by_id = claims_io.index_by_id(claims)
    problems: list[str] = []
    for section in memo_spec.get("sections", []):
        heading = section.get("heading", "?")
        if _has_legacy_points_without_claim_id(section):
            problems.append(f"section '{heading}': a point has no claim_id")
        for cid in _section_cited_ids(section):
            c = by_id.get(cid)
            if c is None:
                problems.append(f"'{cid}' cited in memo but absent from claims.jsonl")
            elif c.get("status") != "verified":
                problems.append(
                    f"'{cid}' cited in memo but status is '{c.get('status')}', not verified"
                )
    return problems


def lint(memo_spec: dict) -> list[str]:
    """Non-fatal structural warnings — flagged, never fatal (mirrors coverage's depth check):

    (a) **Inference-stacking** — >=3 consecutive blockquote ("> ") paragraphs in one section
        body, i.e. a wall of "Our view" judgments with no facts between them.
    (b) **Smuggled figure** — a declarative sentence carrying a ``$``, ``%``, or digit that
        sits OUTSIDE a blockquote and carries NO ``[[token]]`` — an unexplained/uncited number
        shipping as if it were a sourced fact.
    """
    warnings: list[str] = []
    for section in memo_spec.get("sections", []):
        heading = section.get("heading", "?")
        body = section.get("body", "") or ""

        # (a) consecutive blockquote *paragraphs* (blank-line separated), each a run of
        # one-or-more "> " lines. Three or more in a row = inference stacking.
        run = 0
        for para in re.split(r"\n[ \t]*\n", body):
            stripped = para.strip()
            is_quote = bool(stripped) and all(
                ln.lstrip().startswith(">") for ln in stripped.splitlines() if ln.strip()
            )
            if is_quote and stripped:
                run += 1
                if run == 3:
                    warnings.append(
                        f"section '{heading}': 3+ consecutive 'Our view' blockquotes "
                        "(inference-stacking — separate them with the facts they rest on)"
                    )
            else:
                run = 0

        # (b) smuggled figure: a non-blockquote line with a number/$/%, no [[token]].
        for raw in body.splitlines():
            line = raw.strip()
            if not line or line.startswith(">"):  # blank or inside an "Our view" block
                continue
            if line.startswith(("#", "|")) or set(line) <= set("|-: "):
                continue  # headings and table rows/separators aren't prose sentences
            if _TOKEN.search(line):
                continue  # carries a citation
            if _HAS_FIGURE.search(line):
                snippet = " ".join(line.split())[:80]
                warnings.append(
                    f"section '{heading}': figure outside a blockquote with no citation "
                    f"token — \"{snippet}\""
                )
    return warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="Check a memo cites only verified claims.")
    ap.add_argument("--run", required=True)
    ap.add_argument("--memo", required=True, help="memo spec JSON")
    args = ap.parse_args()
    memo_spec = json.loads(Path(args.memo).read_text(encoding="utf-8"))
    problems = check(args.run, memo_spec)
    warnings = lint(memo_spec)

    if warnings:
        print(f"check_memo: {len(warnings)} structural lint warning(s) (non-fatal):",
              file=sys.stderr)
        for w in warnings:
            print(f"  ⚠ {w}", file=sys.stderr)

    if not problems:
        print("check_memo: OK — every cited claim is verified")
        return 0
    print(f"check_memo: FAILED — {len(problems)} problem(s):", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
