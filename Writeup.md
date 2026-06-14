# Writeup — M&A case study tool

*Nicholas Kang · merger-arbitrage analyst case study · worked example: Cintas (CTAS) / UniFirst (UNF)*

---

## Introduction

This tool is an end-to-end agent-orchestration pipeline that turns a one-page deal spec — parties, seed documents, and any analyst steering — into an investment memo. The memo covers two things: **(1) the strategic and financial rationale for the deal, and (2) the tail risks that could derail it** — then synthesizes them into a view on whether the deal closes, recognizing the limitations of doing so.

**This tool augments the analyst; it doesn't replace one.** Its job is to take an uninformed analyst to a defensible understanding of the companies, the industry, the deal, and the macro backdrop in a fraction of the usual time. That frees the analyst's hours for the work the tool can't do: expert judgment and the high-leverage diligence that needs domain expertise and human relationships. The output is a better-researched memo, written faster, for a better investment outcome.

The tool gets better on two levers: **(1)** an analyst tunes the config — the coverage checklist, the source taxonomy, and the method cards that tell the agents how to reason; and **(2)** the underlying models improve under it, lifting every stage at once with no change to the pipeline.

---

## Principles

1. **Human-in-the-loop:** A human gate sits between every stage — the tool proposes an artifact, pauses, and takes the analyst's edits before releasing the next stage.
2. **Auditable:** Every claim is a structured object tagged as either fact or inference, carrying its source and verbatim quote. The entire trail is recorded in `/audit`.
3. **Comprehensive:** A thoughtful assessment requires extensive research, done by giving the human or agent the right mental scaffolding to connect the dots and draw the right inferences.

---

## How it works, end-to-end

Think of it as a small diligence team you direct, where every member shows their work and nobody asserts anything they can't source. You hand it a deal brief (parties, tickers, date, seed documents, your hunches) and start the run. It moves through five stages, stopping at a **human gate** after each one to show its work and take your steering before it proceeds.

```
  /merger-run deal_spec/<deal>.yaml
            │
            ▼
 ┌──────────┐ 🚦 ┌──────────┐ 🚦 ┌──────────┐ 🚦 ┌──────────┐ 🚦 ┌──────────────┐ 🚦
 │1. Intake │ →  │2. Source │ →  │3.Research│ →  │4. Expert │ →  │5. Red-team & │ → final_memo.md
 │  deal    │    │   plan   │    │ fan-out  │    │ skeptical│    │   finalize   │
 │ skeleton │    │ sources +│    │  + verify│    │  draft   │    │attack judg-  │
 │          │    │  key Qs  │    │  + cover │    │   memo   │    │ments + render│
 └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────────┘

  🚦 = human gate: review / edit / steer before the next stage runs.
```

1. **Intake** — reads the brief, extracts the deal skeleton (parties, price, structure, dates), shows you the scope.
2. **Source planning** — proposes the sources it intends to consult, by class, *and* derives the deal-specific first-principles questions the static checklist would miss — all *before* the expensive work, so you're never surprised where a claim came from.
3. **Research** — fans out one researcher per coverage area, in parallel; each extracts facts as quoted snippets with page-level citations, then a central ingest verifies them and throws out anything whose quote can't be found.
4. **Expert analysis** — an expert reads only *verified* facts and writes a skeptical draft memo: deal type, whether the strategic logic holds or is empire-building, premium vs. synergies, and the few risks that matter to *this* deal.
5. **Red-team and finalize** — a fresh skeptic attacks the draft's *judgments*; each critique is resolved (accepted-and-edited or rebutted), and the fail-closed renderer produces the final memo.

**The run lands in two folders:**

- **`/artifacts`** — the human-readable outputs you review at each gate: the source plan, research findings, the **research brief** (after stage 3), the preliminary memo, and most importantly **`final_memo.md`** — the finished product, with an exec summary, deal structure, rationale, a ranked tail-risk section, an assessment with explicit "what would change our view" triggers, and an honest "limits of this assessment."
- **`/audit`** — the structured provenance behind every word of the memo: `claims.jsonl` (the spine), the source registry, the verification and coverage reports, the steering log + full conversation, the per-area research proposals, the cached source snapshots, and the eval scorecard. Nothing in the memo exists here without a traceable origin.

---

## Key design decisions

A master orchestrator (the `merger-run` skill) drives the run: at each of the five stages it invokes that stage's skill, and each skill drives the Python spine through a single CLI (`scripts/cli.py`), which calls the underlying scripts — research ingest, coverage mapping, the memo renderers — and the deterministic hooks (`validate_schema`, `verify_citations`). The **Python-CLI-with-deterministic-hooks** design is deliberate: the load-bearing checks are reproducible code, not model judgment. Stages never talk to each other directly; they communicate only through files on disk.

With that in mind, the four decisions that matter:

**1. The single spine — the memo is a view over a claim store, not freehand prose.** Three files flow through every stage:

- `deal_spec` — all deal-specific input (the only thing you edit per deal).
- `source_registry` — every source, with tier, URL, retrieval time, and content hash.
- `claims.jsonl` — the audit spine; each claim is `{statement, type: fact|inference, supports[], source_ids[], quote, locator, status}`.

A fact without a source and quote is invalid *by schema*; experts may build only on `verified` claims; the renderers assemble verified claims into narrative. There is no code path from an unverified claim to rendered output — which makes "no ungrounded claim reaches the memo" structurally true, not aspirational.

**2. A master orchestrator over agents and subagents.** The orchestrator passes *pointers*, not contents, so it never ingests the full corpus and stays lean across a long multi-stage run; every handoff is an inspectable file. Underneath it, the wide work fans out to subagents — to parallelize effort and limit context bloat:

- Research spawns one subagent per coverage area, each writing grounded claim *proposals* that a separate ingest step then verifies and admits.
- Post-run evaluation fans out one independent verifier per chunk of surfaced claims.

**3. Layered verification — checks of deliberately different kinds, split across two places.**

*In-pipeline:*

- **Deterministic (script, no LLM)** — re-fetches the cited source and confirms the quoted span is physically present at the locator. Catches dead or fabricated citations with certainty.
- **Semantic (model)** — asks whether the source actually *supports* the claim, not just whether it resolves.

*Post-run (out of pipeline):*

- **Independent evaluator** — re-judges every surfaced claim against its *own cached source*, so it doesn't inherit the pipeline's blind spots and can catch **misattribution**: a real, correctly-quoted source cited for a statement it doesn't support.

**4. Page-level citations, quarantining, fail-closed rendering.** Citations resolve to filing section + page, carry their tier inline, and roll up into a "sources consulted" appendix. A citation that fails — dead URL, quote absent, smart-quote mismatch, non-contiguous span — is *quarantined*: kept in the audit trail with a reason, barred from rendering. The renderers refuse to print an unverified claim; during red-team this held even against the tool itself, when a skeptic's benchmark was rebutted *because its supporting evidence had been quarantined*.

---

## The evaluation

Two metrics carry the most weight — **precision** (are the facts accurate?) and **entailment** (do inferences follow from the facts?) — because those are the failure modes a memo can't survive. The rest are secondary: useful, but not where the tool lives or dies.


|               | Metric                                  | What it asks                                                                                 |
| ------------- | --------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Primary**   | **Fact precision**                      | Does the citation resolve, is the quote present, and does it actually support the statement? |
|               | ↳ Fabrication rate                      | Citation dead or absent — the cardinal sin.                                                  |
|               | ↳ Misattribution rate                   | Resolves and quoted correctly, but doesn't support the statement.                            |
|               | **Inference validity** *(entailment)*   | Are the supports verified, and does the conclusion follow?                                   |
| **Secondary** | Separation discipline                   | No opinion dressed up as fact.                                                               |
|               | Coverage                                | Checklist areas with a verified claim.                                                       |
|               | Utilization                             | Did the memo use what it found?                                                              |
|               | Fact / insight recall *(gold set only)* | Did we surface the material facts and reach the key judgments?                               |


These split into **two evals**, because precision and recall have very different costs — a fact has a clean check against its own source, but recall ("did we catch everything?") is unanswerable without knowing what *should* have been found.

**[Live eval] — independent verification, on every memo.**

- *When:* runs on every finished memo, today.
- *How:* re-checks every surfaced claim against its cached source, fanning out parallel verifiers, and writes a reproducible scorecard of fact precision, fabrication, misattribution, inference validity, separation, coverage, and utilization. The coverage/utilization figures are honestly labelled as *recall proxies* — they measure "did we use what we found," not "did we find what exists."

**[Backtest eval] — gold-set recall, in production.**

- *When:* a pinned regression harness — re-run the whole pipeline on a fixed set of deals at regular intervals (and on every model / prompt / pipeline change) to confirm quality holds and nothing regressed.
- *How:* set aside a handful of past investment memos as **golden truths** — closed deals where both the real proxy and a real IC memo exist, annotated for material facts and key judgments. Re-run the pipeline on those deals and compare. All the live-eval metrics, plus:
  - **Fact recall** — did we surface the material facts?
  - **Insight recall** — did we independently reach the key judgments (overpayment, integration, antitrust)? Missing the thesis is a failure, not a blemish.
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

- **Inspectability + GUI.** The audit trail is complete but lives in JSON/markdown. A clickable GUI that makes it trivial to walk from a memo sentence to its claim to its source quote is the single biggest usability lift.
- **A curated knowledge base.** A vetted library the research agents draw on — trustworthy primary sources by sector, the structural questions good diligence asks per area, reusable method cards — raising both recall and analytical quality.
- **Two-way throughput and dialogue.** Parallelize multiple deals in one dashboard; make the gates *two-way* so the analyst can ask their own questions ("show me the comps") and have an agent re-run just the affected stage on feedback.
- **Pipeline improvements:**
  - **Council of advisors across providers.** A single model family is prone to **self-agreement bias** — expert and red-team share a prior. Running expert / red-team / judge across different frontier models buys genuine diversity: convergence means real confidence, divergence flags the contested ground for a human.
  - **The right model for each job.** Assign by purpose rather than use one everywhere — e.g. a multi-modal model for document parsing (pulling figures out of scanned exhibits, charts, and PDF tables that filings bury), a strong reasoning model for the expert and red-team judgment work, and a fast, cheap model for high-volume mechanical checks.
  - **A test-time-compute knob.** Quality is a function of test-time compute — more agents, deeper/longer thinking yield better results. A single knob to dial this per run trades cost for quality on demand.
  - **Self-improvement — close the eval loop.** Learn from mistakes through eval and human feedback, then recursively improve the config.

---

## My own view on Cintas/UniFirst

**I largely agree with the tool's conclusion** — a strategically sound, low-leverage, high-certainty horizontal consolidation at a genuinely full price, where the dominant risks are the antitrust review, Cintas overpaying, and the claimed synergies:

- **Why the antitrust review is now the central risk.** The voluntary HSR **withdraw-and-refile** turned out to be the prelude to a **second request**, which the agencies have now issued. That is the single most important development in the deal. Given more time, this is where I'd dig hardest — the agency's *theory of harm*, whether the route overlap is **national or concentrated in specific metros** (which decides whether targeted divestitures are enough to clear it), the remedy the parties are likely to offer, and the realistic timeline to a decision.
- **Why the valuation is so high.** A ~102.5% premium *above every framework UniFirst's own bankers ran*, with an 8.0x flattered by synergy-inclusive EBITDA, is an outlier. The tool flags it but treats it as a fact to triangulate; I want the *why* — scarcity (the last scaled national platform), pre-empting Elis, or a winner's curse. The escalation path ($255 in 2022 → an advisor calling $275 "very full" → $310) signals real tension, and the answer changes post-close expectations.
- **Whether route density actually materializes when you look closer.** This is the whole strategic case, and the memo *asserts* but doesn't *quantify* it. Uniform rental is a logistics business disguised as a textile one: cost-to-serve is dominated by the drive between stops, so folding a rival's customers onto routes you already run drops marginal cost toward zero — *in theory*. I'd want a **route-overlap analysis**; that single number is the best test of whether the $375M is conservative or heroic, and I won't treat the synergy figure as anything but an unverified management assertion until I see the build-up.

