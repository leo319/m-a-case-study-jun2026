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
   didn't restrict it, cover all `required` + `recommended` areas. **Always also run two
   dedicated context deep-dives** so the brief stands alone and has real depth:
   - **`company_profiles`** — both acquirer and target: reportable segments with revenue in
     `$` and `%`, segment growth, employee/customer counts, and each company's stated
     strategy. (Tag target claims to `target_fundamentals`, acquirer claims to
     `commercial_market`.)
   - **`industry_structure`** — market structure (how many national players vs. the regional
     long tail), secular trends, and **comparable consolidations** (precedent M&A — e.g. prior
     roll-ups, spin-offs, rebuffed approaches). (Tag to `commercial_market`.)

2. **Fan out — one `research-area` subagent per area, spawned in parallel.** Use the
   Task tool with `subagent_type: "research-area"`, one call per area, **in a single
   message** so they run concurrently. Give each worker its `RUN_DIR` and its `AREA`.
   Each worker pulls the deal-wide plan's sources **for its area** AND runs its own open
   searches (the plan is a starting net, not a cap), writes
   `RUN_DIR/audit/research_proposals_<area>.json` (proposals only — they do NOT ingest),
   and returns a short summary + any gap it hit.

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

5. **Write the narrative brief** (the deliverable). Author `RUN_DIR/audit/brief_spec.json`
   covering: Executive summary · The transaction · The companies · Industry & business model ·
   findings per researched area · Preliminary read & coverage.
   - **Lead with narrative prose, but make the numbers scannable.** Use **markdown tables**
     for anything multi-value — e.g. a YoY revenue trend, the segment-revenue mix for each
     company, a comparable-transactions table — and short **bullet lists** for parallel
     points. Don't reduce the whole brief to bullets, and don't bury a 3-year revenue series
     in a sentence.
   - **Depth bar for the two context sections:** *The companies* must give each side's
     **segment revenue mix (`$` and `%`)** and **strategy**, not just a one-liner;
     *Industry & business model* must cover **market structure / number of players, trends,
     and comparable consolidations**. Assume the analyst knows nothing about the companies.
   - Mark each load-bearing fact with a `[[claim_id]]` token. Citation tokens work **inside
     table cells** too. The renderer **refuses** any non-verified citation.
   - **Don't hand-write footnotes or a source list.** The renderer auto-appends a
     **`## Citations`** block — each distinct `(source, locator)` becomes a page-level
     decimal citation (`[3.1]`, `[3.2]`, …; single-locator sources stay `[5]`) — and a
     **`## Sources consulted (N)`** block listing every source. Your job is just to write good
     `[[claim_id]]` tokens and ensure the underlying claims carry **page-level locators**.
   ```bash
   python tool/scripts/cli.py render-brief --run "<RUN_DIR>" --brief "<RUN_DIR>/audit/brief_spec.json"
   ```
   → `RUN_DIR/artifacts/research_brief.md`.

6. Present `research_brief.md` + `coverage_report.md` to the orchestrator. Be honest
   about the gaps the coverage map flags (areas with no verified claims).

## Rules
- Fan out; don't research every area yourself in one context.
- Workers produce proposals; only the parent ingests/verifies (serially).
- Quotes must be verbatim (copied from `inspect`): **exact unicode** (curly quotes/dashes)
  and a **single contiguous span** — the two things that spuriously quarantine real claims.
  Never invent a quote or URL.
- Every fact's `locator` carries a **page number** where the document is paginated — the brief's
  citations are only as useful as the locators behind them.
- Assume the analyst knows nothing about the companies — the brief must orient them cold, with
  tables for the numbers and real depth in the company & industry sections.
- After ingesting, check `verification_report.md`: if a load-bearing claim quarantined on a
  quote mismatch, re-`inspect` for the exact span and re-ingest it under a **fresh claim id**
  (ingest skips ids already in `claims.jsonl`) rather than dropping the finding.
