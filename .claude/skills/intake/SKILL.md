---
name: intake
description: Stage 1 of the merger pipeline — parse a deal_spec, create a run, and present the deal scope for analyst confirmation.
allowed-tools: Bash Read
---

# Stage 1 — Intake & Scoping

Parse the deal spec and create the run. The deal skeleton at this stage is
analyst-provided **seeds**, not yet grounded — research is where seeds become
verified claims.

## Do this

1. Run intake (default deal_spec if none given):
   ```bash
   python tool/scripts/cli.py intake --deal "tool/deal_spec/cintas_unifirst.yaml"
   ```
   The **last stdout line is the run directory** — report it back as `RUN_DIR`; the
   orchestrator needs it for every later stage.

2. Read and present `RUN_DIR/intake.md`: the parties, deal status (signed vs
   proposed vs hypothetical — flag if unknown), seed docs, run config, and the
   analyst's steering notes/priorities.

3. Note explicitly that all headline terms are **seeds to be grounded**, not facts.

Then hand control back to the orchestrator for the gate (confirm scope + steering).
