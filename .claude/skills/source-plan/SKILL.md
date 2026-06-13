---
name: source-plan
description: Stage 2 of the merger pipeline — the PLAN step. Propose the sources research will use AND derive the deal-specific first-principles questions, for the analyst to approve/edit BEFORE research fans out.
allowed-tools: Bash Read Write WebSearch
model: opus
---

# Stage 2 — Plan (sources + first-principles questions)

This is the **Plan** step. Two jobs, one gate:
1. Propose the **sources** research will use, grouped by area/class.
2. Derive the **deal-specific first-principles questions** (`key_questions`) — what the
   static coverage checklist *misses* for THIS deal — so research gathers the right facts and
   the expert can later reason the "why".

The analyst approves / adds / removes / edits both **before** any research fetching. You are
given `RUN_DIR`.

## How to work

1. **Read the scope:** `RUN_DIR/audit/intake.json` (deal, seed_docs, run_config, steering)
   and the deal-agnostic class list:
   ```bash
   python tool/scripts/cli.py source-plan-template
   ```

2. **First-principles pass — derive the `key_questions` (the heart of this stage).** Read the
   method cards in `tool/methodology/` (start with `00_first_principles.md`, then `01`–`05`).
   The static coverage checklist (`python tool/scripts/cli.py coverage-checklist`) is your
   **floor**; the cards are how you find what it misses for *this* deal. Working card by card
   (industry → companies → deal → macro → why), reason from first principles about this
   specific deal and ask **"what does the checklist not anticipate here?"** Produce a focused
   set of questions across the five buckets — especially card 05's **anomaly drill**: scan the
   seed terms for anything that looks off (premium far above precedent, pursuing despite a hard
   regulatory path, buying a declining segment) and turn each into a "why" question for research
   to chase. Don't restate generic checklist subtopics — the `key_questions` are the
   *deal-specific* ones the checklist would miss. Keep them sharp and few (roughly 6–12), each
   tagged to the coverage `area` that will answer it.

3. **Run a broad discovery sweep — find what a fixed checklist misses.** Before planning,
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

4. **Assemble the plan — deal-wide, every source tagged with its `area`.** Cover the areas
   the analyst emphasised (or all required + recommended), **and make sure every
   `key_question` has at least one source meant to answer it.** For each area, mix three kinds:
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
     | merger_agreement | the **merger agreement** (annex to the merger proxy / 424B3, or 8-K exhibit) — its "The Merger Agreement" summary: conditions, termination & break-fee, MAC, regulatory-efforts covenant |
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

5. **Write the plan** to `RUN_DIR/audit/source_plan.json` — one deal-wide list. It carries
   both `key_questions` (step 2) and `planned_sources`, each source tagged with its `area`
   (scout finds carry `"via":"scout"`):
   ```json
   {
     "deal_id": "<deal_id>",
     "key_questions": [
       {"id":"q_<slug>","bucket":"<industry|companies|deal|macro|why>","area":"<coverage_area>",
        "question":"<a deal-specific first-principles question the static checklist would miss>",
        "why_it_matters":"<what answering it decides for the analysis>"}
     ],
     "planned_sources": [
       {"id":"s_<slug>","title":"<source title>","area":"<coverage_area>",
        "class":"<class>","tier":"T1","url":"https://...",
        "rationale":"<why this source answers its area>"},
       {"id":"s_<slug2>","title":"<source surfaced by discovery>","area":"<coverage_area>",
        "class":"<class>","tier":"T2","url":"https://...","via":"scout",
        "rationale":"<non-obvious, found by the sweep rather than the checklist>"}
     ],
     "classes_skipped": [
       {"class":"<class>","reason":"<why it doesn't apply for this deal>"}
     ]
   }
   ```

6. **Persist + render:**
   ```bash
   python tool/scripts/cli.py source-plan --run "<RUN_DIR>" --plan "<RUN_DIR>/audit/source_plan.json"
   ```

7. **Present `RUN_DIR/artifacts/source_plan.md` at the gate.** Walk the analyst through both
   the **`key_questions`** (so they can edit/add/drop the deal-specific questions before any
   fetching) and **what the discovery sweep added beyond seeds + canonical** (the `(via scout)`
   entries). Make skipped classes explicit too.

## Rules

- Sources only — do NOT fetch content or extract claims here. That's research (Stage 3).
- **First principles, not framework-jamming.** The cards are a prompt library, not a checklist
  to fill — derive each question from *this* deal's economics; drop card prompts that don't fit.
- **`key_questions` are the deal-specific delta over the checklist** — sharp and few (~6–12),
  each tagged to an `area`, every one with a source meant to answer it. Don't restate generic
  subtopics; the checklist already covers those.
- One **deal-wide** plan: every planned source carries its `area`.
- Discovery is **breadth, not depth** — surface the non-obvious and cross-area; don't pad the
  plan with low-credibility noise, and leave per-lens deep searching to the research workers.
- Prefer primary (T1 filings/regulators/dockets) for anything load-bearing.
- Surface gaps honestly via `classes_skipped`; the gate is where the analyst fills them.
