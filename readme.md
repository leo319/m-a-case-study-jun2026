# Writeup — M&A case study tool

*Nicholas Kang · merger-arbitrage analyst case study · worked example: Cintas (CTAS) / UniFirst (UNF)*

---

## Executive summary

The tool takes a one-page deal spec — parties, tickers, announcement date, seed documents, and any analyst steering — and produces a final investment memo covering both the deal's strategic/financial rationale and its tail risks. 

Auditability and steerability are key principles of the tool. Concretely, this means gating every stage of the process to get human input and producing intermediate artifacts (e.g., a research brief) and a full audit trail every claim, source, quote, and verification verdict).

On Cintas/UniFirst it concluded — and I largely agree — that this is a high-certainty horizontal consolidation at a very full price: the deal will most likely complete, and the principal concern is that Cintas overpaid rather than that the deal falls apart.

---

## Principles

These are the six principles from the build plan — each one a mechanism in code, not a sentiment:


| Principle             | Mechanism (not a vibe — a thing in code)                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Transparency**      | Every claim is a structured object tagged `fact` vs `inference`, with source + verbatim quote. The memo is a *render* of that store. |
| **Accuracy**          | Deterministic citation verifier (URL resolves + quote present) runs as a hook; failures are quarantined, never shown.                |
| **Comprehensiveness** | A coverage checklist by risk/area, with a "searched / hits / gaps" report so blind spots are visible.                                |
| **Steerability**      | Human gate between every stage; the tool proposes and pauses, never auto-finishes. unless explicitly asked.                          |
| **Customizable**      | `deal_spec` + `run_config` drive everything; deal-specific facts live in config, never in logic.                                     |
| **Auditable**         | Full audit trail.                                                                                                                    |


---

## How it works, end-to-end

Think of it as a small diligence team you direct, where every member shows their work and nobody asserts anything they can't source. You hand it a deal brief (parties, tickers, date, seed documents, your hunches). It runs five stages, stopping to show its work after each:

1. **Intake** — reads the brief, extracts the deal skeleton (parties, price, structure, dates), shows you the scope.
2. **Source planning** — proposes the list of sources it intends to consult, by class, *before* the expensive work, so you're never surprised where a claim came from.
3. **Research** — fans out researchers, one per coverage area, in parallel; each extracts facts as quoted snippets with page-level citations, and verification throws out anything whose quote can't be found.
4. **Expert analysis** — an expert reads only *verified* facts and writes a skeptical draft memo: deal type, whether the strategic logic holds or is empire-building, premium vs. synergies, and the few risks that matter to *this* deal.
5. **Red-team and finalize** — a fresh skeptic attacks the draft's *judgments*; each critique is resolved (accepted-and-edited or rebutted), and the fail-closed renderer produces the final memo.

What lands is a memo with an exec summary, deal structure, rationale, a ranked tail-risk section, an assessment with explicit "what would change our view" triggers, and an honest "limits of this assessment" — every fact cited, every judgment flagged.

---

## Key design decisions

A master orchestrator (the `merger-run` skill) drives the run: at each of the five stages it invokes that stage's skill, and each skill drives the Python spine through a single CLI (`scripts/cli.py`), which in turn calls the underlying scripts — research ingest, coverage mapping, the memo renderers — and the deterministic hooks (`validate_schema`, `verify_citations`). 

Stages never talk to each other directly; they communicate only through files on disk. 

With that in mind, the four decisions that matter:

**1. The single spine — the memo is a view over a claim store, not freehand prose.** Three files flow through every stage:

- `deal_spec` — all deal-specific input (the only thing you edit per deal).
- `source_registry` — every source, with tier, URL, retrieval time, and content hash.
- `claims.jsonl` — the audit spine; each claim is `{statement, type: fact|inference, supports[], source_ids[], quote, locator, status}`.

A fact without a source and quote is invalid by schema; experts may build only on `verified` claims; the renderers assemble verified claims into narrative. There is no code path from an unverified claim to rendered output — which makes "no ungrounded claim reaches the memo" structurally true, not aspirational.

**2. A master orchestrator over agents and subagents.** The orchestrator passes *pointers*, not contents, so it never ingests the full corpus and stays lean across a long multi-stage run; every handoff is an inspectable file. 

Underneath it, the wide work fans out to subagents: (used to parallelize effort and limit context bloat) 

- Research spawns one subagent per coverage area, each writing grounded claim *proposals* that a separate ingest step then verifies and admits.
- Post-run evaluation

**3. Layered verification.** Checks of deliberately different kinds, split across two places:

*In-pipeline checks:*

- **Deterministic (script, no LLM)** — re-fetches the cited source and confirms the quoted span is physically present at the locator. Catches dead/fabricated citations with certainty.
- **Semantic (model)** — asks whether the source actually *supports* the claim, not just whether it resolves.

*Post-run evaluation (out of pipeline):*

- **Independent evaluator** — re-judges every surfaced claim against its *own cached source*, so it doesn't inherit the pipeline's blind spots and can catch **misattribution**: a real, correctly-quoted source cited for a statement it doesn't support.

**4. Page-level citations, quarantining, fail-closed rendering.** Citations resolve to filing section + page, carry their tier inline, and roll up into a "sources consulted" appendix. A citation that fails — dead URL, quote absent, smart-quote mismatch, non-contiguous span — is quarantined: kept in the audit trail with a reason, barred from rendering. The renderers refuse to print an unverified claim; during red-team this held even against the tool itself, when a skeptic's benchmark was rebutted *because its supporting evidence had been quarantined*.

---

## The evaluation


| Metric                                      | What it asks                                                                                 |
| ------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Fact precision**                          | Does the citation resolve, is the quote present, and does it actually support the statement? |
| ↳ **Fabrication rate**                      | Citation dead or absent — the cardinal sin.                                                  |
| ↳ **Misattribution rate**                   | Resolves and quoted correctly, but doesn't support the statement.                            |
| **Inference validity**                      | Are the supports verified and does the conclusion follow?                                    |
| **Separation discipline**                   | No opinion dressed up as fact.                                                               |
| **Coverage**                                | Checklist areas with a verified claim.                                                       |
| **Utilization**                             | Did the memo use what it found?                                                              |
| **Fact / insight recall** *(gold set only)* | Did we surface the material facts and reach the key judgments?                               |


These split into two evals, because precision and recall have very different costs — a fact has a clean check against its own source, but recall ("did we catch everything?") is unanswerable without knowing what *should* have been found.

**[Live eval] — independent verification, on every memo.**

- *When:* runs on every finished memo, today.
- *How:* re-checks every surfaced claim against its cached source, fanning out parallel verifiers, and writes a reproducible scorecard of fact precision, fabrication, misattribution, inference validity, separation discipline, coverage, and utilization. The coverage/utilization figures are honestly labelled as *recall proxies* — they measure "did we use what we found," not "did we find what exists."

**[Ongoing / backtest eval] — gold-set recall, in production.**

- *When:* a pinned regression harness — re-run the whole pipeline on a fixed set of deals at regular intervals (and on every model / prompt / pipeline change) to confirm quality holds and nothing has regressed.
- *How:* set aside a handful of past investment memos as **golden truths** — closed deals where both the real proxy and a real IC memo exist, annotated for material facts and key judgments. Re-run the pipeline on those same deals and compare its output to the golden memo. All the live eval metrics plus 
  - **Fact recall** (did we surface the material facts?), 
  - **Insight recall** (did we independently reach the key judgments — overpayment, integration, antitrust? missing the thesis is a failure, not a blemish), and precision vs. a canonical value. 
  - **Reliability** — run the pipeline N times and report the *spread* of every metric, since a high mean with high variance is untrustworthy.

### What it showed on Cintas/UniFirst — weaknesses included

The run surfaced **81 claims (59 facts, 22 inferences)**, judged by an independent `opus-4-8` pass:

- **Fact precision 93.2%**, with **fabrication 0.0%** — no dead or invented citations, the result that matters most against the cardinal sin.
- **Misattribution 6.8%** — the failures that remain are over-reading, not invention.
- **Inference validity 90.9%**, **separation discipline 100%** — the fact/inference line never broke.
- **Coverage 81.8%** (macro/geopolitical and ESG unsearched, flagged in the memo), **utilization 66.1%**.

The defects share one pattern: **the tool doesn't fabricate, it occasionally over-reads a real source** — stretching a genuine, correctly-quoted span to cover a slightly larger or adjacent claim. The cleanest example: the memo reports Cintas's organic growth as "~6.0%" when the cited 10-K says **8.0%** — a wrong number, left visible in the final memo. This is the harder failure to catch (a casual reader checking the link finds a real document and moves on), which is exactly why the evaluator judges *entailment*, not just resolution — and the fix belongs upstream, in tightening the research/expert re-grounding discipline, not in patching the memo.

---

## What I'd build with more time

- **Inspectability + GUI.** The audit trail is complete but lives in JSON/markdown. Having a clickable GUI that makes it easy to inspect sources is critical.
- **A curated knowledge base.** A vetted library the research agents draw on — trustworthy primary sources by sector, the structural questions a good diligence asks per area, reusable method-cards — raising both recall and analytical quality.
- **A council of advisors across providers.** A single model family is prone to **self-agreement bias** — expert and red-team share a prior. Running expert/red-team/judge across different providers' frontier models buys genuine diversity: convergence means real confidence, divergence flags the contested ground for a human.
- **The right model for each job.** Beyond diversity, different models have different strengths, and I'd assign them by purpose rather than use one everywhere — e.g. Gemini for multi-modality and document parsing (pulling figures out of scanned exhibits, charts, and PDF tables that filings bury), a strong reasoning model for the expert and red-team judgment work, and a fast, cheap model for high-volume mechanical checks.
- **A better UI for throughput and dialogue.** Parallelize multiple deals in one dashboard; make the gates two-way so the analyst can ask their own questions ("show me the comps") and have an agent re-run just the affected stage on feedback.
- **Close the eval loop.** Feed eval findings (like the 6.0%-vs-8.0% miss) back as a bounded repair loop before sign-off, so the eval is a gate, not just a report card.

---

## My own view

**I largely agree with the tool's conclusion** — a strategically sound, low-leverage, high-certainty horizontal consolidation at a genuinely full price, where the dominant risk is that Cintas overpaid and the outcome hinges on whether the under-disclosed ~$375M of synergies arrives on time. The deal will very likely close; the question is what it's worth once it does. But there are contentious areas I'd push harder on before signing my name:

- **Why the valuation is so high.** A ~102.5% premium *above every framework UniFirst's own bankers ran*, with an 8.0x flattered by synergy-inclusive EBITDA, is an outlier. The tool flags it but treats it as a fact to triangulate; I want the *why* — scarcity (the last scaled national platform), pre-empting Elis, or a winner's curse. The escalation path ($255 in 2022 → an advisor calling $275 "very full" → $310) signals real tension, and the answer changes post-close expectations.
- **Why route density and scale are so decisive.** This is the whole strategic case and the memo asserts but doesn't quantify it. Uniform rental is a logistics business disguised as a textile one: cost-to-serve is dominated by the drive between stops, so folding a rival's customers onto routes you already run drops marginal cost toward zero. I'd want a **route-overlap analysis** — that single number is the best test of whether the $375M is conservative or heroic.
- **Macro the tool skipped.** Coverage flagged it as a gap. **Tariffs/supply chain** matter because UniFirst manufactures a meaningful share of its garments, bearing on the margins the deal is priced against; an **Iran/energy** shock cuts both ways (wearer levels vs. UniFirst's own laundering/logistics costs).
- **The people question filings won't answer.** The sale was effectively the **Croatti family's** decision (two-thirds of the vote) — was it a family choosing to sell or being pushed by Engine Capital? In a relationship-driven, route-based business, if tenured drivers and managers are loyal to a family that looks forced out, **attrition risk is real**, and every lost route erodes the density being bought. I'd commission primary diligence here.
- **The antitrust tell I'd chase hardest.** A voluntary HSR **withdraw-and-refile** often precedes a **second request**; if one landed, that's the single development moving this toward genuine break risk. I'd treat the June 11 expiry as the key date, the *reason for the pull* as the key unknown, and — since antitrust in a route business is local — ask whether the overlap is national or concentrated in specific metros.

**Where I'd overrule it:** nowhere on the core thesis — but I'd downgrade the two claims the eval flagged (the 6.0% figure is wrong; the proxy-advisor inference overreaches), and refuse to treat the ~$375M as anything but an unverified management assertion until someone shows me a route-overlap build-up.