---
name: source-plan
description: Stage 2 of the merger pipeline — propose a source list by class for the analyst to approve/edit BEFORE research fans out.
allowed-tools: Bash Read Write WebSearch
model: sonnet
---

# Stage 2 — Source Planning

Propose the sources research will use, grouped by class, so the analyst can approve /
add / remove / edit them **before** any research fetching happens. You are given `RUN_DIR`.

## How to work

1. **Read the scope:** `RUN_DIR/intake.json` (deal, seed_docs, run_config, steering)
   and the deal-agnostic class list:
   ```bash
   python tool/scripts/cli.py source-plan-template
   ```

2. **Propose concrete sources.** For the chosen coverage area, fill each relevant
   class with specific, real sources. Use WebSearch to *locate* concrete documents
   (e.g. the target's latest 10-K on sec.gov) — get direct URLs where you can, or
   leave a `search_hint` for research to resolve. Always carry the seed_docs from
   intake. Give every source a one-line rationale.

   Be honest about coverage: if a class isn't relevant to this area (e.g. court
   dockets for a pure fundamentals pass), list it under `classes_skipped` with a
   reason rather than padding.

3. **Write the plan** to `RUN_DIR/source_plan.json`:
   ```json
   {
     "area": "target_fundamentals",
     "deal_id": "cintas_unifirst",
     "planned_sources": [
       {"id":"s_unf_10k","title":"UniFirst FY2025 Form 10-K","class":"filings","tier":"T1",
        "url":"https://www.sec.gov/Archives/.../unf-20250830.htm",
        "rationale":"Primary source for revenue, margin, organic-growth trend."},
       {"id":"s_news_unf","title":"Recent UniFirst earnings coverage","class":"news_analyst","tier":"T2",
        "search_hint":"UniFirst fiscal 2025 results organic growth","rationale":"Corroborate filings with secondary commentary."}
     ],
     "classes_skipped": [
       {"class":"court_dockets","reason":"Not relevant to a target-fundamentals pass."},
       {"class":"activist_short","reason":"No known activist/short thesis on UNF; revisit in tail-risk."}
     ]
   }
   ```

4. **Persist + render:**
   ```bash
   python tool/scripts/cli.py source-plan --run "<RUN_DIR>" --plan "<RUN_DIR>/source_plan.json"
   ```

5. Present `RUN_DIR/source_plan.md` to the orchestrator for the gate. Make the
   skipped classes explicit so the analyst can add any you left out.

## Rules

- Sources only — do NOT fetch content or extract claims here. That's research (Stage 3).
- Prefer primary (T1 filings/regulators/dockets) for anything load-bearing.
- Surface gaps honestly via `classes_skipped`; the gate is where the analyst fills them.
