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

2. **Propose concrete sources — three kinds, not just given links.** For each area you
   plan to cover, propose a *mix*:
   - **(a) Seeds** — the seed_docs from intake / anything the analyst supplied.
   - **(b) General web search** — at least one `search_hint` per area so research casts
     a wide net (use WebSearch yourself to sanity-check the query returns real results,
     and pin direct URLs where you can).
   - **(c) Canonical / commonsense sources** — the standard places an analyst would
     always check for that area, even if nobody named them. Use this cheat-sheet:

     | Area | Canonical sources to propose |
     |---|---|
     | target_fundamentals | target 10-K + latest 10-Q, earnings releases (8-K Ex-99) |
     | commercial_market | both 10-K "Competition" sections, industry/analyst overviews |
     | deal_rationale_synergies | deal press release, merger proxy / 424B3 "reasons for the merger" |
     | financing_balance_sheet | merger proxy financing section, acquirer debt 8-K, rating-agency actions |
     | antitrust_regulatory | merger proxy "Regulatory Approvals", DOJ/FTC press releases, news on second requests |
     | litigation_legal | 10-K "Legal Proceedings", court dockets (CourtListener), litigation news |
     | management_governance | DEF 14A proxy, executive/board news, leadership-change coverage |
     | short_activist | Seeking Alpha, short-seller reports (e.g. Hindenburg/Muddy Waters), 13D activist filings |
     | macro_geopolitical | 10-K risk factors (FX/tariffs), macro/sector commentary |
     | operational_integration | both 10-Ks (facilities/IT/supply chain), integration commentary in deal materials |
     | esg_environmental | 10-K environmental disclosures, ESG-rating / controversy coverage |

   Give every source a one-line rationale and a tier. Prefer direct URLs; use
   `search_hint` when you can't pin one. Be honest: if an area/class truly doesn't apply,
   list it under `classes_skipped` with a reason rather than padding.

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
