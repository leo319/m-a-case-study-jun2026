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

0. **Use the approved source plan.** Read `RUN_DIR/source_plan.json` (produced by
   Stage 2 and approved at its gate). Ground claims **only** in those approved sources.
   If a source has a `url`, use it; if it only has a `search_hint`, resolve it to a
   direct document URL with WebSearch. Do not invent new sources the analyst didn't
   approve — if you find you need one, say so at the gate rather than adding it silently.

1. **Resolve any source URLs with WebSearch.** Prefer primary sources:
   - SEC filings via EDGAR (the target's latest 10-K/10-Q) — these are **T1**.
   - Major news / reputable secondary — **T2**. Trade press — **T3**. Blogs/forums — **T4**.
   Get **direct document URLs** (e.g. `sec.gov/Archives/.../xxx.htm`), not search-results
   or `cgi-bin` pages — the verifier re-fetches the exact URL you cite.

2. **Read sources with `inspect`, NOT WebFetch.** SEC.gov (and many sites) return
   **HTTP 403 to WebFetch**. To read a document's text, use the spine's fetch path:
   ```bash
   # surface candidate verbatim sentences containing any of these terms:
   python tool/scripts/cli.py inspect --url "<direct url>" --grep "revenue|organic|margin|retention|competi"
   # or dump the first chunk of extracted text:
   python tool/scripts/cli.py inspect --url "<direct url>"
   ```
   **Copy your quotes verbatim from `inspect` output.** It extracts text exactly the
   way the verifier does, so a span copied from `inspect` is guaranteed to match.
   For each fact, copy a verbatim quote that supports it (an approximate paraphrase
   will be quarantined). Add inferences only as `type: inference` building on fact ids.

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

   **Cover context, not just the area's numbers.** Assume the analyst knows little
   about these companies. Your claims must let the brief explain: what the deal is
   (parties, structure, headline value), what each company does, the industry/business
   model, and then the area's findings. Ground the context too (e.g. the target's
   business description and the deal terms from filings/press releases).

5. **Ingest + verify** writes `RUN_DIR/research_findings.md` (the verified-claims
   appendix) and `RUN_DIR/verification_report.md` (what was **quarantined and why**).

6. **Write the narrative brief.** The deliverable is `research_brief.md` — a readable
   briefing, NOT a bullet list. Author `RUN_DIR/brief_spec.json`:
   ```json
   {"title":"Research brief — <deal>: <area>", "subtitle":"...",
    "sections":[
      {"heading":"Executive summary","body":"<prose with inline [[c01]] citations>"},
      {"heading":"The transaction","body":"..."},
      {"heading":"The companies","body":"..."},
      {"heading":"Industry & business model","body":"..."},
      {"heading":"<Area> findings","body":"..."},
      {"heading":"Preliminary read & gaps","body":"..."}
    ]}
   ```
   In `body`, mark each load-bearing fact with a `[[claim_id]]` token — it expands to a
   cited footnote and the renderer **refuses** any non-verified citation. Then render:
   ```bash
   python tool/scripts/cli.py render-brief --run "<RUN_DIR>" --brief "<RUN_DIR>/brief_spec.json"
   ```

7. Present `RUN_DIR/research_brief.md` to the orchestrator, and be honest about
   coverage gaps (what you could not source). The findings appendix and
   `verification_report.md` back it up.

## Rules

- Never invent a quote or a URL. If you can't find a real source, leave the claim out
  — a quarantined fabrication is worse than a gap.
- Quotes must be exact. Whitespace differences are tolerated; wording changes are not.
- Don't over-claim: one fact = one source + one quote.
