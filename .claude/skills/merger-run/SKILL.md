---
name: merger-run
description: Run the merger-analysis pipeline for a deal — orchestrates intake → research → expert → memo with a human gate after every stage. User-invoked only.
disable-model-invocation: true
allowed-tools: Bash Read Write Skill Glob
---

# Merger Analysis — Run Orchestrator

You are the **master orchestrator**. You manage control flow across the pipeline,
run each stage by invoking its skill, and **stop at a human gate after every stage**.
You never run the whole pipeline to the end on your own.

The substantive logic lives in `tool/` (Python). You drive it via one CLI:
`python tool/scripts/cli.py <command>`. All paths are relative to the repo root.

## STEP 0 — Always start by showing the full journey

Before doing anything, run:

```bash
python tool/scripts/cli.py map
```

Show the analyst that pipeline map verbatim, then tell them plainly:
- This is the **whole journey** so they know what to expect.
- **Active now**: Intake, Source Planning, Research, Expert, Red-Team & Finalize.
- The pipeline ends with a red-team pass (an independent skeptic attacks the memo's
  judgments) and a final memo.
- After **every** stage you will stop, show them the artifact, and wait for their
  steering before continuing.

Ask which deal_spec to run (default: `tool/deal_spec/cintas_unifirst.yaml`). Then proceed.

## The gate protocol (do this after EVERY stage)

A "gate" works with Claude Code's turn-taking:
1. Run the stage; it writes artifacts into the run directory.
2. **Present** a concise summary of the artifact + where it lives, and state any
   gaps/quarantines honestly.
3. **Record** the gate to the audit log (do this when the analyst replies):
   ```bash
   python tool/scripts/cli.py gate --run "<RUN_DIR>" --stage <stage> \
     --presented "<what you showed>" --steering "<their reply verbatim>" \
     --artifacts "<file1,file2>"
   ```
4. **Stop and wait** for the analyst's reply. Do not start the next stage until they
   approve. Fold their steering into the next stage.

## Control flow

1. **Intake** — invoke the `intake` skill with the chosen deal_spec. It prints the
   run directory on its last line — **capture it as `RUN_DIR`** and reuse it for
   every later command. Present `intake.md`. 🚦 Gate.

2. **Source Planning** — invoke the `source-plan` skill with `RUN_DIR`. It proposes
   the sources research will use, by class, and lists classes it skipped. Present
   `source_plan.md` and **make the skipped classes explicit** so the analyst can add
   any that are missing. 🚦 Gate (approve / add / remove / edit sources). This gate
   happens **before** any research fetching.

3. **Research** — invoke the `research` skill with `RUN_DIR`. It **fans out one
   `research-area` subagent per coverage area** (parallel leaf workers), grounds claims
   only in the **approved** sources from `source_plan.json`, tags each claim with its
   area, ingests + verifies centrally, and builds the coverage map:
   ```bash
   python tool/scripts/cli.py coverage --run "<RUN_DIR>"
   ```
   Present `research_brief.md`, the verification summary (**what was quarantined and
   why**), and `coverage_report.md` — call out the **gaps (blind-spot areas)** so the
   analyst can direct more research. 🚦 Gate.

4. **Expert** — invoke the `expert` skill with `RUN_DIR`. It produces the preliminary
   memo (verified claims only; the renderer refuses anything ungrounded). Present
   `preliminary_memo.md`. 🚦 Gate (review the preliminary analysis, steer).

5. **Red-Team & Finalize** — invoke the `red-team` skill with `RUN_DIR`. An independent
   skeptic attacks the memo's judgments (`redteam_critique.json`); you resolve each finding
   and render `final_memo.md` (still fail-closed). Present `final_memo.md` with the red-team
   ledger (findings by severity, accepted vs. rebutted, what changed). 🚦 Gate (final sign-off).

6. Tell the analyst the run is complete and point them to the audit trail:
   `steering_log.md`, `conversation.jsonl`, `claims.jsonl`, `source_registry.json`,
   `verification_report.md`, `redteam_critique.json` in `RUN_DIR`.

## Rules

- One `RUN_DIR` for the whole run; never mix runs.
- Never present or rely on a quarantined/unverified claim. If a stage quarantined
  something the analyst cares about, say so and offer to re-research it.
- Keep your gate summaries short and honest. Surface gaps; don't paper over them.
