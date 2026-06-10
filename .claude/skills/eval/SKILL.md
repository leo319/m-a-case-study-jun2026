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
   This reads every `chunk_NN_result.json`, computes the metrics, and writes the scorecard
   + ledger. It reuses the pipeline's own coverage + utilization helpers, so those numbers
   match the run's coverage report.

4. **Present the results.** Show `RUN_DIR/eval/scorecard.md` in full, then the top
   (failures-first) rows of `RUN_DIR/eval/ledger.md`. Be honest about any FABRICATION /
   MISATTRIBUTION / WEAK-INFERENCE / DISCIPLINE flags and any surfaced claim that received
   no verdict.

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
  ledger.md                # per-claim verdicts, failures first (🔴 for fabrications)
  scorecard.md             # headline rates with raw counts + one honest read
  scorecard.json           # machine mirror (feeds eval-dashboard)
```

## Metrics (all guard divide-by-zero → `n/a`)
- **fact precision** = facts PASS / facts total
- **fabrication rate** = facts FABRICATION / facts total
- **misattribution rate** = facts MISATTRIBUTION / facts total
- **inference validity** = inferences PASS / inferences total
- **separation discipline** = inferences NOT flagged DISCIPLINE / inferences total
- **coverage%** and **utilization** are reused from the pipeline's coverage helpers.

## Rules
- Standalone: do NOT wire this into `merger-run`; do NOT mutate the run's claims/memo.
- The verdict is judged against the **cached snapshot**, not the live web — reproducible.
- Each verifier is independent: it judges a claim against its own source only, never the
  memo narrative. Don't collapse the fan-out into one context.
