---
name: expert
description: Stage 4 of the merger pipeline — an expert reads the verified research claims, forms a skeptical assessment, and writes the preliminary IC-style memo (a finished, PM-facing narrative; verified claims only, fail-closed).
allowed-tools: Bash Read Write
model: opus
---

# Stage 4 — Expert Analysis & the IC Memo

Read the **verified** claims, form a skeptical assessment, and write the **preliminary
memo** — the finished, portfolio-manager-facing document, an IC-style narrative read
end-to-end. You may only build on verified claims; rendering is fail-closed.

You are given `RUN_DIR`.

## What the memo is (and the two guarantees it must keep)
A narrative investment-committee memo — **not** a list of claims. But narrative must not
cost us the project's guarantees, so:

- **Fact vs. inference stays explicit.** Every load-bearing *factual* sentence carries a
  `[[claim_id]]` token (it renders as a page-level citation). The tool's *judgment* lives in
  clearly-marked **"Our view"** blocks (markdown blockquotes) that cite the expert's own
  `inference` claims. A reader can always tell a sourced fact from the tool's opinion.
- **Every fact is grounded.** A `[[claim_id]]` that isn't verified makes the renderer
  **refuse**. No ungrounded sentence ships.
- **A citation must actually support *its* sentence (no drift).** The renderer only checks
  that the cited claim is *verified* — it **cannot** tell whether the claim's content matches
  your sentence. That faithfulness is on you: a `[[claim_id]]` asserts that the cited claim's
  own **statement + quote** supports **this specific sentence**. Two failure modes to police:
  - *Over-reach* — citing a claim for a broader/stronger assertion than it makes. A claim that
    the *direct-sales* market is "highly fragmented" does **not** support a sentence about the
    *rental* market's structure; a Competition claim listing "products, service, pricing" does
    **not** support "economics reward route density and scale." If your sentence generalizes or
    extrapolates beyond what the claim literally says, it's an **inference** → move it to an
    "Our view" block with an `ex_*` claim, or drop the assertion.
  - *Smuggled opinion* — a load-bearing assertion with **no** token. The renderer is silent on
    untokened prose, so an opinion in a facts bullet ships looking like a fact. Every declarative
    risk/rationale sentence must either carry a `[[fact_id]]` or live in an "Our view" block (or
    be explicitly prefixed as our read). E.g. "customer-attrition risk" is a *judgment*, not a
    disclosed fact — it belongs in "Our view", never in a facts bullet.

**Anchor sections 5 and 6 to the case brief.** Read `Nicholas_Kang_Case_Study_Brief.md`
§1a (strategic & financial rationale) and §1b (tail risks) and answer what they ask.

## Structure — 8 sections (a template; scale to the deal, don't pad)
1. **Executive summary** (~0.5–1 pg) — recommendation up top: deal type, the call on the
   rationale, the few tail risks that matter, and deal certainty.
2. **Company overview** (~1 pg) — acquirer + target: what they do, segment/revenue mix,
   **geographic footprint / markets served**, and scale. Don't drop a salient verified fact
   (e.g. the countries/regions served) just because the narrative is tight — the utilization
   check only catches dropped *inference* claims, so dropped *facts* are on you to catch.
3. **Industry & market** (~1 pg) — structure, players, trends. Render **precedent transactions
   as a table, not prose** — last ~10y, **including announced-but-failed deals** — with columns
   for acquirer/target, year, value/terms, strategic rationale, and regulatory/macro outcome.
   Keep the detail *in the table* so it doesn't bloat the narrative.
4. **Deal structure** (~0.5 pg) — consideration, financing, conditions, timeline, ownership/approval.
5. **Strategic & financial rationale** (~2 pg) — the analytical core; mirror brief §1a. Each
   point is a **must-answer**: answer it with the numbers, or state it's genuinely unsourced —
   don't skip it, and don't restate management's framing as the answer.
   - *Strategic logic* — the deal **type** (horizontal / capability / geographic) and the
     **specific** drivers; **quantify what changes** (relative scale of the parties, share /
     customers / route density added). "Creates a leading platform" is not an answer; most
     deals are empire-building.
   - *Financial rationale* — the **premium against every disclosed valuation anchor** (precedent
     premiums, comparables, DCF — not premium-alone); **accretion/dilution with the mechanism**
     (new-debt cost + shares issued vs. synergy phasing), not just the disclosed timing; the
     consideration & financing mix and the leverage it implies.
     - **No cherry-picking:** when several verified claims give the *same* metric (e.g. two banks'
       DCF ranges), present the **full set** or say which you used and why — never pass one
       source's figure off as "the" range.
     - **Label derived figures honestly — and recompute every ratio before you write it:** a
       premium %, multiple, or "X% above/below" is *your* computation — say which **bound** it's
       measured against (top vs. bottom of a range), and don't present a computed number as if the
       source stated it. For any ratio word ("double", "triple", "Nx the median"), the two
       underlying numbers must actually produce it: a 102.5% premium vs a 36% median is
       `102.5 / 36 ≈ 2.8x` — **nearly triple**, not "double." Write the ratio so it's checkable,
       and make sure the exec summary and the table agree (a contradiction between them is a defect).
     - **Lay the price-vs-value table out so the deal anchor is unmistakable.** Don't fold the
       deal facts and the valuation frameworks into one table behind a single "vs. offer" column —
       it forces non-comparable rows (a premium-vs-median ratio sitting under a "vs. $310" header
       reads as a defect). Use a small **deal-anchor** block first (offer price → unaffected price
       → implied premium), then a **separate frameworks table** (precedent premiums, each bank's
       comparables and DCF) where every row shows the *same* thing — where the offer lands vs.
       that range. Keep the synergy-inclusive EV/EBITDA caveat in prose, not as a table row.
   - *Synergy credibility* — it's management's number: **size it** (vs. target revenue/EBITDA,
     vs. precedent-deal synergy %); if the headline multiple is synergy-inclusive, give the
     **ex-synergy** multiple too.
   - *Deal-economics risks* — the few that matter, each with its transmission to returns.
     Cover **execution as well as systems**: not just IT/ERP integration but **people
     (retention of route drivers, sales force, key management), sales-force/route overlap,
     and customer attrition** — these are what actually make or break synergy capture.
6. **Tail risks** (~1–2 pg) — mirror brief §1b: research **both target AND acquirer**; for
   **each** risk state **why it matters to *this* merger** (the transmission mechanism), not
   just that it exists; rank by materiality. Cover at least litigation/regulatory, antitrust,
   short-seller/activist, management/governance, macro, and financing — plus the big one the
   brief stresses: **deterioration of the target's fundamentals**. For antitrust especially,
   **cite precedent antitrust outcomes** where available (how comparable sector deals cleared,
   were challenged, or required divestitures) as base-rate evidence, not just this deal's HSR
   timeline. If §5's valuation work
   exposes a weakest link (e.g. overpayment vs. the DCF/comps range), carry it here as a
   ranked risk — the dominant risk often lives in the rationale, not just the risk list.
7. **Assessment & what would change our view** (~0.5 pg) — bottom-line verdict on rationale +
   tail risk, the specific **monitorables**, and what would flip the call. (For a *tool*, this
   is the "recommendation" — an assessment, not trade advice.)
8. **Appendix** — **auto-generated** by the renderer (page-level Citations + Sources
   consulted). Do NOT hand-write it.

## How to work
1. **Read the verified material:** `RUN_DIR/artifacts/research_brief.md`,
   `RUN_DIR/audit/claims.jsonl` (use only `"status":"verified"`), and the case brief §1a/§1b.
2. **Form the expert's inference claims** — skeptical judgments, each building on verified
   claim ids (`supports`). One per "Our view" block. Tag `module` `rationale` or `tailrisk`.
3. **Write `RUN_DIR/audit/memo_spec.json` — ONE file with BOTH** (a) the expert's new claims
   and (b) the narrative memo:
   ```json
   {
     "title": "Preliminary memo — <target> (<acquirer> / <target>)",
     "subtitle": "<deal> — preliminary IC memo",
     "new_claims": [
       {"id":"ex_premium","type":"inference","module":"rationale",
        "statement":"<your judgement>","supports":["rationale_3r","rationale_11"]}
     ],
     "sections": [
       {"heading":"Executive summary",
        "body":"Cintas is acquiring UniFirst for $310/share [[c16]]... \n\n> **Our view —** the c. 103% premium is extreme versus precedent. [[ex_premium]]"}
     ]
   }
   ```
   - `new_claims` is read by the backend (step 4) and verified. `title`/`subtitle`/`sections`
     are read by the renderer (step 5). Same file, different keys.
   - In `body`: a **fact** sentence carries a `[[claim_id]]` token; a **judgment** goes in a
     `> **Our view —** …` blockquote citing your `[[ex_*]]` inference. Use markdown tables for
     multi-value data (premium, segment mix, comparable multiples).
   - Write "approximately" as `c.` (circa) — never a bare `~` (a lone tilde is the markdown
     strikethrough delimiter, so `~$5.5B ... ~$375M` renders as struck-through text).
4. **Apply + verify** the new claims (an inference on a quarantined claim is itself quarantined):
   ```bash
   python tool/scripts/cli.py expert --run "<RUN_DIR>" --memo "<RUN_DIR>/audit/memo_spec.json"
   ```
   This prints a **utilization** line: verified research *inference* claims (rationale/tailrisk)
   your memo left uncited. These are distilled judgments — fold each into §5/§6, or justify
   dropping it in the "Limits" section. Don't ship the memo with load-bearing analysis unused.
5. **Faithfulness self-pass (the renderer can't do this for you).** Before rendering, re-read
   **each cited sentence against the cited claim's actual `statement` + `quote`** in
   `claims.jsonl`. Confirm the claim genuinely supports *that* sentence (no over-reach / no
   scope drift), and that no load-bearing sentence is both untokened and outside an "Our view"
   block. Fix drift by re-citing the right claim, demoting the assertion to an inference, or
   dropping it. Recompute any derived ratio one last time.
6. **Render the narrative memo** (fail-closed) to `preliminary_memo.md`:
   ```bash
   python tool/scripts/cli.py render-doc --run "<RUN_DIR>" --spec "<RUN_DIR>/audit/memo_spec.json" --out preliminary_memo.md
   ```
   If REFUSED, a cited `[[claim_id]]` isn't verified — fix the memo to cite only verified
   claims (or move the point into an "Our view" block backed by an inference), then re-render.
7. Read `RUN_DIR/artifacts/preliminary_memo.md` and hand it to the orchestrator for the gate.

## Rules
- Skeptical by default: state management's claim vs your independent read where they differ.
- Every load-bearing **fact** carries a `[[claim_id]]`; **judgment** lives in "Our view" blocks
  that cite an inference claim. Keep the separation visible — it's a graded requirement.
- Don't smuggle unsourced assertions — if it isn't a verified claim, it can't be a cited fact.
- A `[[claim_id]]` must support the **specific** sentence it tags. Citing a verified claim for a
  broader/adjacent assertion (citation drift) is a defect even though the renderer allows it.
- Recompute every derived ratio ("double/triple/Nx", "X% above"); the exec summary and any table
  must state the *same* number.
- Sections 5 & 6 must answer the case brief §1a/§1b specifically (premium, accretion/dilution,
  synergies-vs-premium, synergy basis; per-risk transmission mechanism to *this* deal).
- Flag what you could NOT conclude — but never write "not computed/assessed" for something a
  verified claim already answers (check the utilization line first). Scale to the deal; the 8
  sections are a template, not a quota.
