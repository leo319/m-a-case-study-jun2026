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

1. **Read the scope:** `RUN_DIR/audit/intake.json` (deal, seed_docs, run_config, steering)
   and the deal-agnostic class list:
   ```bash
   python tool/scripts/cli.py source-plan-template
   ```

2. **Run a broad discovery sweep — find what a fixed checklist misses.** Before planning,
   run ~6–10 open WebSearch queries across both companies + the deal, hunting the
   **non-obvious, cross-area** sources a class list won't predict:
   - activist / hedge-fund campaigns (a fund's press releases, `PREC14A` / `DFAN14A` /
     Schedule 13D filings),
   - short-seller reports,
   - **comparable / precedent deals** (prior roll-ups, spin-offs, rebuffed approaches),
   - regulator statements, and pivotal news.

   Pin each to a **direct URL** where you can, else leave a `search_hint`. **Noise
   discipline:** prefer primary; for any secondary candidate name the specific publisher
   and why it's credible; never list aggregators / SEO / AI-summary pages; tier honestly.
   Tag everything this sweep surfaces (beyond seeds + the cheat-sheet) with `"via":"scout"`.
   Keep it to **breadth** — leave per-lens deep searching to the Stage-3 research workers.

3. **Assemble the plan — deal-wide, every source tagged with its `area`.** Cover the areas
   the analyst emphasised (or all required + recommended). For each area, mix three kinds:
   - **(a) Seeds** — the seed_docs from intake / anything the analyst supplied.
   - **(b) Discovery** — the relevant candidates from your sweep (tagged `"via":"scout"`).
   - **(c) Canonical / commonsense sources** — the standard places an analyst would
     always check for that area, even if nobody named them. Use this cheat-sheet:

     | Area | Canonical sources to propose |
     |---|---|
     | target_fundamentals | target 10-K + latest 10-Q, earnings releases (8-K Ex-99) |
     | commercial_market | both 10-K "Competition" sections, industry/analyst overviews |
     | deal_rationale_synergies | deal press release; 424B3 "Background of the Merger" + **"Opinion of the Financial Advisor"** (premium, comparable-companies / precedent-transactions / DCF multiples, accretion view); the target's **unaffected pre-announcement share price** (for the premium) |
     | financing_balance_sheet | merger proxy financing section, acquirer debt 8-K, rating-agency actions |
     | antitrust_regulatory | merger proxy "Regulatory Approvals", DOJ/FTC press releases, news on second requests |
     | litigation_legal | 10-K "Legal Proceedings", court dockets (CourtListener), litigation news |
     | management_governance | DEF 14A proxy, executive/board news, leadership-change coverage |
     | short_activist | Seeking Alpha, short-seller reports (e.g. Hindenburg/Muddy Waters), 13D activist filings |
     | macro_geopolitical | 10-K risk factors (FX/tariffs), macro/sector commentary |
     | operational_integration | both 10-Ks (facilities/IT/supply chain), integration commentary in deal materials |
     | esg_environmental | 10-K environmental disclosures, ESG-rating / controversy coverage |

   Give every source an `area`, a `class`, a `tier`, and a one-line rationale. Prefer
   direct URLs; use `search_hint` when you can't pin one. Be honest: if an area/class
   truly doesn't apply, list it under `classes_skipped` with a reason rather than padding.

4. **Write the plan** to `RUN_DIR/audit/source_plan.json` — one deal-wide list, each entry
   carrying its `area` (scout finds carry `"via":"scout"`):
   ```json
   {
     "deal_id": "cintas_unifirst",
     "planned_sources": [
       {"id":"s_unf_10k","title":"UniFirst FY2025 Form 10-K","area":"target_fundamentals",
        "class":"filings","tier":"T1","url":"https://www.sec.gov/Archives/.../unf-20250830.htm",
        "rationale":"Primary source for revenue, margin, organic-growth trend."},
       {"id":"s_engine_prec14a","title":"Engine Capital PREC14A","area":"short_activist",
        "class":"filings","tier":"T2","url":"https://www.sec.gov/Archives/...","via":"scout",
        "rationale":"Activist pushing the board to sell — surfaced by discovery, not the checklist."}
     ],
     "classes_skipped": [
       {"class":"court_dockets","reason":"No live litigation surfaced; revisit if research finds any."}
     ]
   }
   ```

5. **Persist + render:**
   ```bash
   python tool/scripts/cli.py source-plan --run "<RUN_DIR>" --plan "<RUN_DIR>/audit/source_plan.json"
   ```

6. **Present `RUN_DIR/artifacts/source_plan.md` at the gate.** Explicitly call out **what the
   discovery sweep added beyond seeds + canonical** (the `(via scout)` entries) so the analyst
   can steer — prioritise, drop, or add — before any research fetches. Make skipped classes
   explicit too.

## Rules

- Sources only — do NOT fetch content or extract claims here. That's research (Stage 3).
- One **deal-wide** plan: every planned source carries its `area`.
- Discovery is **breadth, not depth** — surface the non-obvious and cross-area; don't pad the
  plan with low-credibility noise, and leave per-lens deep searching to the research workers.
- Prefer primary (T1 filings/regulators/dockets) for anything load-bearing.
- Surface gaps honestly via `classes_skipped`; the gate is where the analyst fills them.
