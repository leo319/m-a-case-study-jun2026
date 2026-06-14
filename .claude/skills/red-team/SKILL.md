---
name: red-team
description: Stage 5 of the merger pipeline — an independent skeptic attacks the preliminary memo's judgments, then you resolve each critique and render the final memo (verified claims only, fail-closed).
allowed-tools: Bash Read Write Agent
model: opus
---

# Stage 5 — Red-Team & Finalize

An independent skeptic attacks the expert's **judgments** (not its verified facts); you
then resolve each critique honestly, **close the unanswered "whys" you can from the existing
fact base**, and render `final_memo.md`. There is **no research loop-back** — anything that
can't be answered from existing verified claims becomes an explicit **Limitations** entry.

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

2b. **Close the unanswered "whys" (the gap hunt).** Independently of the skeptic's findings,
   list the **logical gaps and unanswered "whys"** the memo still has — start from the Plan
   stage's `key_questions` (`RUN_DIR/audit/source_plan.json`) and the memo's own open threads
   (an asserted judgment with no mechanism, an anomaly noted but not explained). For **each**:
   - **Try to close it from the existing fact base** — search the verified claims
     (`claims.jsonl`, `status:verified`) for evidence that lets you form a grounded inference,
     and if you can, add a `rt_*` inference claim and fold the answer into the memo.
   - **If it can't be closed**, do **not** loop back to research — record it as an explicit
     **Limitations** entry (see step 4). A named gap in understanding is the honest outcome.
3. **Write the resolution back** into `redteam_critique.json` — add `"resolution": "accepted | rebutted"`
   and `"resolution_note": "<what you changed, or why it doesn't hold>"` to each finding. This is
   the audit trail of the red-team's effect.
4. **Build `RUN_DIR/audit/final_memo_spec.json`** — copy `memo_spec.json`, **retitle it**
   ("Final memo …" / "final IC memo, post red-team" — don't inherit "Preliminary"), then apply
   your accepted edits to the section bodies and append any new `rt_*` inference claims to `new_claims`
   (each `supports` only **verified** claim ids — same rules as the expert stage). Leave
   `preliminary_memo.md` and `memo_spec.json` untouched so the before/after stays visible.
   - **Add / extend a `## Limitations` section** at the end of the memo body (before the
     auto-generated appendix). List every "why" / `key_question` you could **not** close from
     the fact base (step 2b) and every accepted `missing` counter-point you couldn't ground —
     each as one honest line naming the gap in understanding. This is where unanswerable "whys"
     land; never paper over them and never invent a source to fill them.
5. **Apply + verify** the new claims, then **render fail-closed**:
   ```bash
   python tool/scripts/cli.py expert    --run "<RUN_DIR>" --memo "<RUN_DIR>/audit/final_memo_spec.json"
   python tool/scripts/cli.py render-doc --run "<RUN_DIR>" --spec "<RUN_DIR>/audit/final_memo_spec.json" --out final_memo.md
   ```
   If render REFUSES, a cited `[[claim_id]]` isn't verified — fix the citation (or move the point
   into an "Our view" block backed by a verified inference) and re-render.
6. Read `RUN_DIR/artifacts/final_memo.md` and present it for the **final sign-off** gate, with a
   short ledger: findings by severity, which you accepted vs. rebutted, **which "whys" you
   closed from the fact base vs. moved to Limitations**, and what changed.

## Rules
- The skeptic attacks judgment; you never weaken the fact/inference + fail-closed guarantees.
- **Flag mis-framed risks.** Any item presented as a "risk" that actually favors or de-risks the
  deal is mis-framed — it should be reclassified (and explained as such), not listed as a risk.
- **Close, don't loop.** Try to answer each unanswered "why" / `key_question` from existing
  verified claims (grounded `rt_*` inference); never re-open research. Unclosable → Limitations.
- **Check entailment, not just facts.** Beyond closing "whys", make sure each load-bearing
  conclusion you keep **follows from its premises** — if the skeptic flags a leap (a conclusion
  resting on an unstated premise, or one question's answer standing in for another's — e.g. a
  strong strategic rationale treated as if it settled close likelihood), close it by grounding the
  missing premise or softening the conclusion. The fail-closed rails check facts; logical validity
  is on you.
- The expert's authoring rules still bind to every section body you edit: **no citation drift**
  (a `[[claim_id]]` must support the specific sentence it tags), **no untokened opinion** in a
  facts bullet (judgments go in "Our view"), and **recompute any derived ratio** you touch. Run
  the same faithfulness self-pass — re-read each cited sentence against the claim's `statement` +
  `quote` — before you render `final_memo.md`.
- Don't rubber-stamp: if you rebut a finding, the note must say *why*, citing evidence.
- Prefer honest caveats over deletion — surfacing a limitation is better than hiding a weak point.
- Keep `preliminary_memo.md` intact; the final memo is a **separate** artifact.
