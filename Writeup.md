# Writeup — M&A case study tool

*Nicholas Kang · merger-arbitrage analyst case study · worked example: Cintas (CTAS) / UniFirst (UNF)*

---

## What this tool is for

It answers the two questions a merger-arbitrage analyst has to answer about a deal: does the strategic and financial **rationale** hold, and what **tail risks** could derail it. It takes a one-page deal spec — parties, tickers, announcement date, seed documents, and any steering the analyst wants to add — and produces an investment memo on both, with every fact traced to a source.

It does not replace the analyst. It augments one. It compresses the time from a deal announcement to a defensible understanding, and it does the mechanical work — sourcing, quoting, verifying, cross-checking, mapping coverage — so the analyst spends their hours on judgment and the few high-leverage calls a human with domain expertise and accountability should own.

A domain expert improves it through two levers: the **per-deal inputs and config** they tune (what to emphasize, which sources to trust, which questions this specific deal demands), and the **model underneath**, which gets better over time while the pipeline's structure stays fixed. Tuning the first is the analyst's daily craft; the second is upside they get for free.

On Cintas/UniFirst it concluded — and I largely agree — that this is a high-certainty horizontal consolidation at a very full price. The deal will most likely complete; the principal concern is that Cintas overpaid, not that the deal breaks.

---

## Principles

Three commitments, each one a mechanism in code rather than a sentiment.

**Human-in-the-loop and steerable.** A human gate sits between every stage: the tool proposes an artifact, pauses, and takes the analyst's edits before releasing the next stage. `deal_spec` + `run_config` drive everything, and the analyst's steering propagates from intake to every downstream stage. Nothing deal-specific lives in the logic, so re-pointing the tool at a new deal means editing inputs, not code.

**Auditable.** Every claim is a structured object tagged `fact` vs `inference`, carrying its source and a verbatim quote. The memo is a *render* of that claim store, not freehand prose — so for any sentence you can trace the source, the quote, and the verification verdict. Every run also records the analyst's steering turns, so an auditor can replay exactly what the human directed.

**Robust and comprehensive.** A coverage checklist scores each risk/area as searched / hits / gaps, so blind spots are visible instead of silent. A deterministic citation verifier runs as a hook — a claim whose URL is dead or whose quote can't be found is quarantined, never rendered. There is no code path from an unverified claim to the memo.

---

## How it works

Five stages, each followed by a human gate. Two design choices run through all of them: **work is broken into small, independently-verifiable chunks** — narrow enough that each agent does its piece well, and aggregated centrally — and **independent chunks run in parallel** for speed.

1. **Intake** — reads the brief, extracts the deal skeleton (parties, price, structure, dates) as grounded claims, and shows you the scope.
2. **Source planning** — proposes the sources it intends to consult, by class, *before* the expensive work, and derives the deal-specific questions this deal demands that the static checklist would miss. You approve, add, or cut.
3. **Research** — fans out one researcher per coverage area in parallel; each extracts facts as quoted snippets with page-level citations. Verification then throws out anything whose quote can't be found in its source.
4. **Expert analysis** — an expert reads *only verified* facts and writes a skeptical draft: deal type, whether the strategic logic holds or is empire-building, premium vs. synergies, and the few risks that matter to *this* deal.
5. **Red-team and finalize** — a fresh skeptic attacks the draft's *judgments*; each critique is resolved (accepted-and-edited or rebutted with reasoning), and the fail-closed renderer produces the final memo.

The output is a memo with an exec summary, deal structure, rationale, a ranked tail-risk section, an assessment with explicit "what would change our view" triggers, and an honest "limits of this assessment" — every fact cited, every judgment flagged.

---

## Key design decisions

A master orchestrator (the `merger-run` skill) drives the run: at each stage it invokes that stage's skill, which drives a Python spine through one CLI (`scripts/cli.py`) and its deterministic hooks (`validate_schema`, `verify_citations`). Stages never talk to each other directly — they communicate only through files on disk.

**1. One spine: the memo is a view over a claim store.** Three files flow through every stage:

- `deal_spec` — all deal-specific input (the only thing you edit per deal).
- `source_registry` — every source, with tier, URL, retrieval time, and content hash. Fetched docs are cached content-addressed, so the eval is deterministic even as the live web changes.
- `claims.jsonl` — the audit spine; each claim is `{statement, type: fact|inference, supports[], source_ids[], quote, locator, status}`.

A fact without a source and quote is invalid by schema. Experts may build only on `verified` claims. The renderers assemble verified claims into narrative. Because there is no code path from an unverified claim to rendered output, "no ungrounded claim reaches the memo" is a structural property, not a hope.

**2. A thin orchestrator over fan-out subagents.** The orchestrator passes *pointers*, not contents, so it never ingests the full corpus and stays lean across a long multi-stage run; every handoff is an inspectable file. Underneath it, wide work fans out: research spawns one subagent per coverage area, each writing grounded claim *proposals* that a separate ingest step verifies and admits. The same fan-out pattern runs the post-run evaluation.

**3. Layered verification — checks of deliberately different kinds, split across two places.**

*In-pipeline:*
- **Deterministic (script, no LLM)** — re-fetches the cited source and confirms the quoted span is physically present at the locator. Catches dead or fabricated citations with certainty.
- **Semantic (model)** — asks whether the source actually *supports* the claim, not just whether it resolves.

*Out-of-pipeline (post-run eval):*
- **Independent evaluator** — re-judges every surfaced claim against its *own cached source*, so it doesn't inherit the pipeline's blind spots. This is what catches **misattribution**: a real, correctly-quoted source cited for a statement it doesn't support.

**4. Page-level citations, quarantine, fail-closed rendering.** Citations resolve to filing section + page and carry their tier inline. A citation that fails — dead URL, absent quote, smart-quote mismatch, non-contiguous span — is quarantined: kept in the audit trail with a reason, barred from the memo. The renderers refuse to print an unverified claim. This held even against the tool itself: during red-team, a skeptic's benchmark was rebutted *because its supporting evidence had been quarantined*.

---

## Evaluation

The two dimensions are verifiable in different ways, so the eval splits in two. A fact has a clean check against its own source. Recall — "did we find everything that exists?" — has no answer without knowing what *should* have been found. We don't conflate them.

| Metric | What it asks |
|---|---|
| **Fact precision** | Does the citation resolve, is the quote present, and does it support the statement? |
| ↳ **Fabrication rate** | Citation dead or absent — the worst failure mode. |
| ↳ **Misattribution rate** | Resolves and quoted correctly, but doesn't support the statement. |
| **Inference validity** | Are the supports verified, and does the conclusion follow? |
| **Separation discipline** | No opinion dressed up as fact. |
| **Coverage / utilization** | Checklist areas with a verified claim; did the memo use what it found. |
| **Fact / insight recall** *(gold set only)* | Did we surface the material facts and reach the key judgments? |

**Live eval — independent verification, on every memo.** Runs today, on every finished run. It re-checks every surfaced claim against its cached source, fans out parallel verifiers, and writes a reproducible scorecard. Coverage and utilization are labelled honestly as *recall proxies* — they measure "did we use what we found," not "did we find what exists."

**Backtest eval — gold-set recall, for production.** A pinned regression harness: set aside closed deals where both the real proxy and a real IC memo exist, annotate them for material facts and key judgments, re-run the pipeline, and compare. It adds **fact recall** (did we surface the material facts), **insight recall** (did we independently reach the key judgments — overpayment, integration, antitrust; missing the thesis is a failure, not a blemish), and **reliability** — run N times and report the *spread*, since a high mean with high variance is untrustworthy.

### What it showed on Cintas/UniFirst — weaknesses included

The run surfaced **81 claims (59 facts, 22 inferences)**, judged by an independent `opus-4-8` pass:

- **Fact precision 93.2%**, **fabrication 0.0%** — no dead or invented citations, the result that matters most.
- **Misattribution 6.8%** — the failures that remain are over-reading, not invention.
- **Inference validity 90.9%**, **separation discipline 100%** — the fact/inference line never broke.
- **Coverage 81.8%** (macro/geopolitical and ESG unsearched, flagged in the memo), **utilization 66.1%**.

Two weaknesses came out of this, and they are different in kind.

**It over-reads a real source.** The tool doesn't fabricate; it occasionally stretches a genuine, correctly-quoted span to cover a slightly larger or adjacent claim. The cleanest example: the memo reports Cintas's organic growth as "~6.0%" when the cited 10-K says **8.0%** — a wrong number, left visible in the final memo. This is the hard failure to catch: a reader who clicks the link finds a real document and moves on. That is exactly why the evaluator judges *entailment*, not just resolution, and the fix belongs upstream — tightening re-grounding discipline in research and expert, not patching the memo.

**It traces logic in a straight line; it doesn't ask why.** The more important weakness is one the metrics above only partly capture. The tool reasons from facts to conclusions competently, but it lacks the reflex a skilled analyst has: when an inference has a gap — a number asserted without a mechanism, a claim that *almost* follows but skips a step — a human gets curious and skeptical, fans out to new research to close it, and loops back. The tool largely doesn't. It runs the trace forward and, where it can't close a gap from the existing fact base, it caveats it in the Limitations section rather than going to find the missing piece. This is partly by design — the pipeline deliberately has no open-ended research loop-back, to stay reproducible — but the cost is real: it surfaces gaps honestly without resolving them, which is precisely the high-leverage work that separates a good analyst from a thorough one. Closing this is the single biggest lever on the tool's analytical quality (see "Close the eval loop" and "curated knowledge base" below).

---

## What I'd build next

- **Inspectability and a GUI.** The audit trail is complete but lives in JSON and markdown. A clickable interface to inspect any claim's source and quote is the most direct way to make the auditability usable.
- **A test-time-compute knob.** Quality scales with test-time compute — more agents, deeper thinking. Exposing that as a dial lets the analyst trade cost for depth per deal.
- **A curated knowledge base.** A vetted library the research agents draw on — trustworthy primary sources by sector, the structural questions good diligence asks per area, reusable method-cards — raising both recall and analytical quality, and directly addressing the straight-line-logic weakness by giving the tool a standing set of "whys" to chase.
- **A council of advisors across providers.** One model family shares a prior, so expert and red-team are prone to self-agreement. Running expert / red-team / judge across different providers' frontier models buys genuine diversity: convergence means real confidence, divergence flags contested ground for a human.
- **The right model for each job.** Beyond diversity, assign models by strength — e.g. a strong multi-modal model to pull figures out of scanned exhibits, charts, and PDF tables that filings bury; a strong reasoning model for expert and red-team judgment; a fast, cheap model for high-volume mechanical checks.
- **A two-way UI for throughput and dialogue.** Run multiple deals in one dashboard; make the gates two-way, so the analyst can ask their own questions ("show me the comps") and have an agent re-run just the affected stage.
- **Close the eval loop.** Feed eval findings (like the 6.0%-vs-8.0% miss, or an unresolved entailment gap) back as a bounded repair loop before sign-off, so the eval is a gate, not just a report card.

---

## My own view

**I largely agree with the tool's conclusion** — a strategically sound, low-leverage, high-certainty horizontal consolidation at a genuinely full price, where the dominant risk is overpayment and the outcome hinges on whether the under-disclosed ~$375M of synergies arrives on time. The deal will very likely close; the question is what it's worth once it does. But there are contested areas I'd push harder on before signing my name.

- **Why the valuation is so high.** A ~102.5% premium *above every framework UniFirst's own bankers ran*, on an 8.0x multiple flattered by synergy-inclusive EBITDA, is an outlier. The tool flags it but treats it as a fact to triangulate. I want the *why*: scarcity (the last scaled national platform), pre-empting Elis, or a winner's curse. The escalation path ($255 in 2022 → an advisor calling $275 "very full" → $310) signals real tension, and the answer changes post-close expectations.
- **Why route density is so decisive.** This is the whole strategic case, and the memo asserts it without quantifying it. Uniform rental is a logistics business disguised as a textile one: cost-to-serve is dominated by the drive between stops, so folding a rival's customers onto routes you already run drives marginal cost toward zero. I'd want a **route-overlap analysis** — that single number is the best test of whether $375M is conservative or heroic.
- **The macro the tool skipped.** Coverage flagged it as a gap. **Tariffs and supply chain** matter because UniFirst manufactures a meaningful share of its own garments, which bears on the margins the deal is priced against. An **energy shock** cuts both ways: it depresses industrial wearer levels but also raises UniFirst's own laundering and logistics costs.
- **The people question filings won't answer.** The sale was effectively the **Croatti family's** call (two-thirds of the vote). Was it a family choosing to sell, or one pushed out by Engine Capital? In a relationship-driven, route-based business, if tenured drivers and managers are loyal to a family that looks forced out, **attrition risk is real**, and every lost route erodes the density being bought. I'd commission primary diligence here.
- **The antitrust tell.** A voluntary HSR **withdraw-and-refile** often precedes a **second request**; if one landed, that is the single development moving this toward genuine break risk. I'd treat the expiry date as the key date, the *reason for the pull* as the key unknown, and — since antitrust in a route business is local — ask whether the overlap is national or concentrated in specific metros.

**Where I'd overrule it:** nowhere on the core thesis. But I'd downgrade the two claims the eval flagged (the 6.0% figure is simply wrong; the proxy-advisor inference overreaches), and I'd refuse to treat the ~$375M as anything but an unverified management assertion until someone shows me a route-overlap build-up.
