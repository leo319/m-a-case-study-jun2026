---
name: eval
description: Live independent verification eval (STANDALONE, not part of merger-run) — re-judges every claim a finished memo surfaced against its own cached source, fanning out parallel verifier subagents, then writes a scorecard (fact precision, fabrication, misattribution, inference validity, separation discipline).
allowed-tools: Bash Read Write Task
model: opus
---

# Eval — independent verification of a finished run

This is a **standalone quality harness**, NOT a pipeline stage — it does not appear in
`merger-run` and it never edits a run's claims or memo. It audits a finished run: it
re-derives the claims the memo actually **surfaced** (cited via `[[id]]` tokens in the
memo spec) and has independent verifier subagents re-judge each one against its **own
cached source snapshot**. Because everything is judged against the snapshot, the eval is
**reproducible** — the same run scores identically every time.

## Inputs
- `RUN_DIR` — the run directory to evaluate (e.g. `tool/runs/<deal>/<ts>`). If not given,
  **ask** for it before doing anything.

## Flow

1. **Plan the eval** — derive the surfaced claims and split them into chunks:
   ```bash
   python tool/scripts/cli.py eval-plan --run "<RUN_DIR>"
   ```
   Then read `RUN_DIR/eval/manifest.json`. It lists `n_chunks` and, under `chunks`, each
   chunk's `file` path and `claim_ids`. (Use `--chunk-size N` to change the default of 10.)

2. **Fan out one `claim-verifier` subagent per chunk — ALL IN ONE MESSAGE (parallel).**
   Use the Task tool with `subagent_type: "claim-verifier"`, one call per chunk, **in a
   single message** so they run concurrently. Give each worker:
   - `RUN_DIR`, and
   - its `CHUNK_FILE` (the chunk's `file` from the manifest, e.g.
     `RUN_DIR/eval/chunks/chunk_00.json`).
   Each worker judges its claims **independently** (it must NOT read any memo narrative)
   and writes `RUN_DIR/eval/chunks/chunk_NN_result.json`.

3. **Aggregate** once all workers have returned:
   ```bash
   python tool/scripts/cli.py eval-aggregate --run "<RUN_DIR>"
   ```
   This reads every `chunk_NN_result.json`, computes the metrics, and writes
   `scorecard.md` (a summary table on top, the full per-claim ledger below). It reuses the
   pipeline's own coverage + utilization helpers, so those numbers match the run's coverage
   report.

4. **Present the results.** Show `RUN_DIR/eval/scorecard.md` — the summary table first, then
   the failures-first rows of its ledger. Be honest about any FABRICATION / MISATTRIBUTION /
   WEAK-INFERENCE / DISCIPLINE flags and any surfaced claim that received no verdict.

5. **Offer the dashboard** (cross-run view): ask whether to run
   ```bash
   python tool/scripts/cli.py eval-dashboard
   ```
   → `tool/runs/_eval_dashboard.md` (one row per run with a scorecard).

## `run/eval/` layout (all generated output)
```
RUN_DIR/eval/
  manifest.json            # deal, run, surfaced/fact/inference counts, chunk list, snapshot hashes
  chunks/
    chunk_00.json          # {"chunk":0,"claims":[<full claim records>]}   (input to a verifier)
    chunk_00_result.json   # {"chunk":0,"verdicts":[...]}                  (verifier output)
    ...
  scorecard.md             # summary table (Primary/Secondary metrics · score · what-failed) + full per-claim ledger
  scorecard.json           # machine mirror (feeds eval-dashboard)
```

## Metrics (all guard divide-by-zero → `n/a`)

**Primary**
- **Precision** = facts PASS / facts total — does the citation resolve, is the quote present, and does it actually support the statement?
  - ↳ **Fabrication rate** = facts FABRICATION / facts total — citation dead or absent.
  - ↳ **Misattribution rate** = facts MISATTRIBUTION / facts total — resolves and quoted correctly, but doesn't support the statement.
- **Inference validity (entailment)** = inferences PASS / inferences total — are the supports verified, and does the conclusion follow?

**Secondary**
- **Separation discipline** = inferences NOT flagged DISCIPLINE / inferences total — no opinion dressed up as fact.
- **Coverage** = checklist areas with ≥1 verified claim (reused from the pipeline's coverage helper).
- **Utilization** = verified rationale/tailrisk research claims the memo cited (reused from the pipeline's helper) — did the memo use what it found?
- **Fact / insight recall (gold set only)** = (material facts surfaced + key judgments reached) / gold-set total — did we surface the material facts and reach the key judgments? Computed only when a gold set is supplied for the deal; `n/a` otherwise.

## Rules
- Standalone: do NOT wire this into `merger-run`; do NOT mutate the run's claims/memo.
- The verdict is judged against the **cached snapshot**, not the live web — reproducible.
- Each verifier is independent: it judges a claim against its own source only, never the
  memo narrative. Don't collapse the fan-out into one context.
