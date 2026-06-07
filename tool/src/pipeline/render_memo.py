"""Render the preliminary memo from a memo spec — fail-closed.

The memo is a *render* of the claim store (PLAN.md §1): every point in the memo
references a claim id, and the renderer pulls the statement + citation from the
verified claim. Before rendering it runs the check_memo guard; if the spec cites
any non-verified claim, it refuses to render and exits 1. So the deliverable
cannot contain an ungrounded sentence — the property is enforced here, not hoped for.

CLI:
  python -m src.pipeline.render_memo --run RUNDIR --memo memo_spec.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..core import claims as claims_io
from ..core import registry as registry_io
from ..core.paths import claims_path, out_path, registry_path
from ..hooks import check_memo


def render(run_dir: str | Path, memo_spec: dict) -> str:
    run_dir = Path(run_dir)
    problems = check_memo.check(run_dir, memo_spec)
    if problems:
        raise ValueError("memo cites non-verified claims:\n  - " + "\n  - ".join(problems))

    claims = claims_io.load_claims(claims_path(run_dir))
    by_id = claims_io.index_by_id(claims)
    sources = registry_io.load_registry(registry_path(run_dir))

    lines = [f"# {memo_spec.get('title', 'Preliminary memo')}", ""]
    if memo_spec.get("subtitle"):
        lines += [f"_{memo_spec['subtitle']}_", ""]
    lines += ["> Every claim below is tagged `fact`/`inference` and traces to a "
              "machine-verified source. This is a render of the verified claim store.", ""]

    footnotes: list[str] = []
    fn_index: dict[str, int] = {}

    def cite(claim: dict) -> str:
        sid = (claim.get("source_ids") or [None])[0]
        if not sid:
            return ""
        if sid not in fn_index:
            s = sources.get(sid, {})
            fn_index[sid] = len(footnotes) + 1
            footnotes.append(f"[^{fn_index[sid]}]: [{s.get('tier','?')}] {s.get('title','?')} — {s.get('url','?')}")
        return f"[^{fn_index[sid]}]"

    for section in memo_spec.get("sections", []):
        lines += [f"## {section.get('heading','')}", ""]
        for pt in section.get("points", []):
            c = by_id[pt["claim_id"]]
            tag = "fact" if c.get("type") == "fact" else "inference"
            marker = cite(c) if c.get("type") == "fact" else ""
            lines.append(f"- **[{tag}]** {c['statement']}{marker}")
        lines.append("")

    if footnotes:
        lines += ["---", ""] + footnotes + [""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render preliminary memo (fail-closed on unverified citations).")
    ap.add_argument("--run", required=True)
    ap.add_argument("--memo", required=True)
    args = ap.parse_args()
    memo_spec = json.loads(Path(args.memo).read_text(encoding="utf-8"))
    try:
        md = render(args.run, memo_spec)
    except ValueError as e:
        print(f"render_memo: REFUSED — {e}", file=sys.stderr)
        return 1
    out = out_path(args.run, "preliminary_memo.md")
    out.write_text(md, encoding="utf-8")
    print(f"render_memo: wrote {out}", file=sys.stderr)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
