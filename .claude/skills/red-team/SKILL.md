---
name: red-team
description: Stage 5 of the merger pipeline — an independent skeptic attacks the preliminary memo's judgments, then you resolve each critique and render the final memo (verified claims only, fail-closed).
allowed-tools: Bash Read Write Agent
model: opus
---

# Stage 5 — Red-Team & Finalize

An independent skeptic attacks the expert's **judgments** (not its verified facts); you
then resolve each critique honestly and render `final_memo.md`. There is **no research
loop-back** — gaps that can't be answered from existing verified claims become caveats.

You are given `RUN_DIR`.

## How to work
1. **Spawn one `skeptic` subagent** (fresh context — independence is the point). Give it
   `RUN_DIR` and tell it to write `RUN_DIR/audit/redteam_critique.json`. Wait for it.
   ```
   Agent(subagent_type="skeptic", prompt="RUN_DIR = <RUN_DIR>. Red-team this memo per your instructions; write audit/redteam_critique.json and return your summary.")
   ```
2. **Read `RUN_DIR/audit/redteam_critique.json`.** For **each** finding, decide:
   - **Accept** → fix the memo: `soften`/`downgrade`/`add-caveat` the wording, or for a
     genuinely new judgment add a `rt_*` inference claim. A `missing` counter-point you accept
     but can't ground from verified claims becomes an explicit line in the memo's "Limits".
   - **Rebut** → leave the memo as is, and record *why* the critique doesn't hold.
   Be honest: a skeptic finding you can't cleanly rebut should change the memo.
3. **Write the resolution back** into `redteam_critique.json` — add `"resolution": "accepted | rebutted"`
   and `"resolution_note": "<what you changed, or why it doesn't hold>"` to each finding. This is
   the audit trail of the red-team's effect.
4. **Build `RUN_DIR/audit/final_memo_spec.json`** — copy `memo_spec.json`, **retitle it**
   ("Final memo …" / "final IC memo, post red-team" — don't inherit "Preliminary"), then apply
   your accepted edits to the section bodies and append any new `rt_*` inference claims to `new_claims`
   (each `supports` only **verified** claim ids — same rules as the expert stage). Leave
   `preliminary_memo.md` and `memo_spec.json` untouched so the before/after stays visible.
5. **Apply + verify** the new claims, then **render fail-closed**:
   ```bash
   python tool/scripts/cli.py expert    --run "<RUN_DIR>" --memo "<RUN_DIR>/audit/final_memo_spec.json"
   python tool/scripts/cli.py render-doc --run "<RUN_DIR>" --spec "<RUN_DIR>/audit/final_memo_spec.json" --out final_memo.md
   ```
   If render REFUSES, a cited `[[claim_id]]` isn't verified — fix the citation (or move the point
   into an "Our view" block backed by a verified inference) and re-render.
6. Read `RUN_DIR/artifacts/final_memo.md` and present it for the **final sign-off** gate, with a
   short ledger: findings by severity, which you accepted vs. rebutted, and what changed.

## Rules
- The skeptic attacks judgment; you never weaken the fact/inference + fail-closed guarantees.
- The expert's authoring rules still bind to every section body you edit: **no citation drift**
  (a `[[claim_id]]` must support the specific sentence it tags), **no untokened opinion** in a
  facts bullet (judgments go in "Our view"), and **recompute any derived ratio** you touch. Run
  the same faithfulness self-pass — re-read each cited sentence against the claim's `statement` +
  `quote` — before you render `final_memo.md`.
- Don't rubber-stamp: if you rebut a finding, the note must say *why*, citing evidence.
- Prefer honest caveats over deletion — surfacing a limitation is better than hiding a weak point.
- Keep `preliminary_memo.md` intact; the final memo is a **separate** artifact.
