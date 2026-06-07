---
name: render-memo
description: Render the preliminary memo from a memo spec — fail-closed, so it refuses to render any claim that is not verified.
allowed-tools: Bash Read
---

# Render Memo (fail-closed)

Render `preliminary_memo.md` from a memo spec. The memo is a *render of the verified
claim store*: every point cites a claim id, and the renderer pulls the statement +
citation from the verified claim. If the spec cites any non-verified claim, it
**refuses** (exit 1) — an ungrounded sentence cannot reach the deliverable.

Normally the `expert` skill calls this for you. To run it directly:

```bash
python tool/scripts/cli.py render --run "<RUN_DIR>" --memo "<RUN_DIR>/memo_spec.json"
```

If it is REFUSED, check which claim id is unverified:

```bash
python tool/scripts/cli.py check-memo --run "<RUN_DIR>" --memo "<RUN_DIR>/memo_spec.json"
```

Fix the memo spec to cite only verified claims, then re-render. Output is
`RUN_DIR/preliminary_memo.md`.
