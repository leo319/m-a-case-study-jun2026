---
name: research
description: Stage 3 of the merger pipeline — research one coverage area, extract grounded claims with verbatim quotes, and run deterministic verification.
allowed-tools: Bash Read Write WebSearch WebFetch
model: sonnet
---

# Stage 3 — Research, Grounding & Verification

Research ONE coverage area for the deal (default: **target fundamentals** —
is the target's business deteriorating? revenue/margin/organic-growth trend,
customer retention, competitive position). Extract claims, each grounded in a
**verbatim quote** from a real source, then let the deterministic verifier judge them.

You are given `RUN_DIR` by the orchestrator.

## How to work

1. **Find sources.** Use WebSearch + WebFetch. Prefer primary sources:
   - SEC filings via EDGAR (the target's latest 10-K/10-Q) — these are **T1**.
   - Major news / reputable secondary — **T2**. Trade press — **T3**. Blogs/forums — **T4**.
   Use **direct document URLs**, not search-results pages — the verifier re-fetches
   the exact URL you cite.

2. **Extract claims.** For each fact, copy a **verbatim quote** from the source that
   supports it — exact characters (the verifier checks the quote is literally present
   in the fetched page; an approximate paraphrase will be quarantined). Add inferences
   only as `type: inference` that build on your fact claim ids.

3. **Write proposals** to `RUN_DIR/research_proposals.json`:
   ```json
   {
     "area": "target_fundamentals",
     "proposals": [
       {"claim_id":"c0001","type":"fact","module":"research",
        "statement":"<plain statement>",
        "source":{"id":"s_unf_10k","title":"<title>","url":"<direct url>","tier":"T1"},
        "quote":"<verbatim span copied from the source>",
        "locator":"<section, optional>"},
       {"claim_id":"c0010","type":"inference","module":"research",
        "statement":"<reasoning>","supports":["c0001"]}
     ]
   }
   ```
   Use `c0001`, `c0002`, … for claim ids and `s_...` for source ids (reuse the same
   source id when several claims cite one document).

4. **Ingest + verify** (this fetches, caches, and checks every quote):
   ```bash
   python tool/scripts/cli.py research --run "<RUN_DIR>" --proposals "<RUN_DIR>/research_proposals.json"
   ```

5. **Read the results** and report them to the orchestrator:
   - `RUN_DIR/research_brief.md` — the verified findings.
   - `RUN_DIR/verification_report.md` — what was **quarantined and why** (dead links,
     quotes not found), tier distribution, counts.
   Be honest about coverage gaps (what you could not source).

## Rules

- Never invent a quote or a URL. If you can't find a real source, leave the claim out
  — a quarantined fabrication is worse than a gap.
- Quotes must be exact. Whitespace differences are tolerated; wording changes are not.
- Don't over-claim: one fact = one source + one quote.
