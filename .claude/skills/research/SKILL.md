---
name: research
description: Stage 3 of the merger pipeline — fan out one research subagent per coverage area, then ingest, verify, map coverage, and write the narrative brief.
allowed-tools: Bash Read Write Task WebSearch
model: opus
---

# Stage 3 — Research, Grounding & Verification (fan-out)

Research the coverage areas **in parallel** — one subagent per area — so no single
context gets bogged down, then ingest everything centrally and verify. You are given
`RUN_DIR`. You orchestrate; the `research-area` workers do the per-area legwork.

## How to work

1. **Choose the areas to cover.** List the checklist (`python tool/scripts/cli.py
   coverage-checklist`). Cover the areas the analyst emphasized in `run_config`; if they
   didn't restrict it, cover all `required` + `recommended` areas. Always include enough
   context areas (deal terms, company descriptions, industry) for the brief to stand alone.

2. **Fan out — one `research-area` subagent per area, spawned in parallel.** Use the
   Task tool with `subagent_type: "research-area"`, one call per area, **in a single
   message** so they run concurrently. Give each worker its `RUN_DIR` and its `AREA`.
   Each worker writes `RUN_DIR/audit/research_proposals_<area>.json` (proposals only —
   they do NOT ingest) and returns a short summary + any gap it hit.

3. **Ingest each area's proposals SERIALLY** (avoid racing on claims.jsonl):
   ```bash
   python tool/scripts/cli.py research --run "<RUN_DIR>" --proposals "<RUN_DIR>/audit/research_proposals_<area>.json"
   ```
   Run once per area's file. This fetches/caches/verifies and writes the verified-claims
   appendix `RUN_DIR/artifacts/research_findings.md` + `RUN_DIR/audit/verification_report.md`.

4. **Build the coverage map:**
   ```bash
   python tool/scripts/cli.py coverage --run "<RUN_DIR>"
   ```
   → `RUN_DIR/audit/coverage_report.md` (searched / hits / gaps).

5. **Write the narrative brief** (the deliverable — readable, NOT a bullet list).
   Author `RUN_DIR/audit/brief_spec.json` covering: Executive summary · The transaction ·
   The companies · Industry & business model · findings per researched area · Preliminary
   read & coverage. Mark each load-bearing fact with a `[[claim_id]]` token (it expands to
   a cited footnote; the renderer **refuses** any non-verified citation). Then:
   ```bash
   python tool/scripts/cli.py render-brief --run "<RUN_DIR>" --brief "<RUN_DIR>/audit/brief_spec.json"
   ```
   → `RUN_DIR/artifacts/research_brief.md`.

6. Present `research_brief.md` + `coverage_report.md` to the orchestrator. Be honest
   about the gaps the coverage map flags (areas with no verified claims).

## Rules
- Fan out; don't research every area yourself in one context.
- Workers produce proposals; only the parent ingests/verifies (serially).
- Quotes must be verbatim (copied from `inspect`); never invent a quote or URL.
- Assume the analyst knows nothing about the companies — the brief must orient them cold.
