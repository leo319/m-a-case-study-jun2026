# Merger Analysis Tool — Build Plan

_Status: draft for review. Worked example: Cintas (CTAS) / UniFirst (UNF). Must generalize to any deal._

---

## 1. Design philosophy (what every decision serves)

The brief's single worst failure is **fabricated or dead citations**. So the architecture's first job is to make it *structurally impossible* for an unsourced or ungrounded claim to reach the final memo — not to ask a model nicely to cite well. Everything below follows from that.

Six principles → six mechanisms:

| Principle | Mechanism (not a vibe — a thing in code) |
|---|---|
| Transparency | Every claim is a structured object tagged `fact` vs `inference`, with source + verbatim quote. The memo is a *render* of that store. |
| Guardrails / accuracy | Deterministic citation verifier (URL resolves + quote present) runs as a hook; failures are quarantined, never shown. |
| Comprehensiveness | A coverage checklist by risk/area, with a "searched / hits / gaps" report so blind spots are visible. |
| Human-in-the-loop | Named human gate between every stage; tool proposes and pauses, never auto-finishes. |
| Customizable | `deal_spec` + `run_config` drive everything; deal-specific facts live in config, never in logic. |
| Trustworthy | Separate eval pipeline over a frozen source snapshot; re-runs to the same verdict. |

---

## 2. The spine: one data model flowing through all stages

These three files are the source of truth. Memos are views over them.

- **`deal_spec.yaml`** — inputs: acquirer, target, tickers, announcement date, seed docs/URLs, known terms; plus `run_config` (depth, areas to emphasize, analyst steering inputs). *This is also what delivers generalization — nothing company-specific lives in the logic.*
- **`source_registry.json`** — every source: `{id, title, url, tier, retrieved_at, content_hash, local_path}`. Fetched docs are cached content-addressed → eval is deterministic even as the live web changes.
- **`claims.jsonl`** — the audit spine. Each claim:
  ```
  {id, statement, type: fact|inference, supports:[claim_ids],
   source_ids:[...], quote, locator, confidence,
   module: research|rationale|tailrisk, status: verified|quarantined|unverified}
  ```
  `fact` claims must carry a source + quote. `inference` claims must reference the `supports` claims they're built on. Experts may only build on `status: verified` claims.

Source tiers (for "a court filing is not a blog post"): **T1** primary (SEC filings, court dockets, regulator releases) > **T2** reputable secondary (major news, sell-side research) > **T3** trade press / specialist > **T4** unverified (blogs, forums). Tier travels with every claim.

---

## 3. The pipeline (5 stages + a gate after each)

Built directly on your structure. "Gate" = tool pauses, presents a structured artifact, takes human add/remove/edit/steer before proceeding.

### Orchestration model: a thin master agent over decoupled stages

Stages are **decoupled** — each reads its inputs from files and writes its outputs to files (`claims.jsonl`, `source_registry.json`, stage artifacts). They never share a live context window. A **master orchestrator agent** sits on top and does only three things, so its own context stays lean:

1. Reads the completed `deal_spec`/`run_config` and **plans the run** — which stages, which coverage areas, which methodology cards apply to this deal.
2. **Dispatches each stage in sequence**, passing only file *pointers* (not full contents) to the stage's worker agent(s), which load what they need.
3. **Runs the human gates** — presents each stage's artifact for review, collects steering, and only then releases the next stage.

This is the `financial-services` managed-agent pattern (orchestrator + depth-1 leaf workers + steering events). The win: the orchestrator never ingests the full research corpus, so it can run a long multi-stage job without context bloat, and every handoff is an inspectable file. **Each stage (and the pipeline as a whole) is packaged as an invokable skill**, so the orchestrator fires "the right agent + its tools" by name — and part of implementation is deciding, per stage, whether an off-the-shelf skill (e.g. from `financial-services`) works or we author one together.

**Stage 1 — Intake & Scoping** _(lightweight)_
Parse `deal_spec`, fetch seed docs (merger proxy/424B3, latest 10-K/10-Q of both, deal deck/press release), extract the deal skeleton (parties, structure, dates, headline terms) as grounded claims.
The analyst can also **steer from the start**: attach their own starting documents, drop in comments/hunches, and set priorities (e.g. "focus on antitrust," "I'm worried about the target's fundamentals"). These steering inputs are stored in `run_config` and propagate to every downstream stage, so the pipeline biases toward what the human already cares about.
→ **Gate:** confirm deal scope + run_config + steering inputs.

**Stage 2 — Source Planning**
Deterministic baseline source list by class (filings, court dockets, regulators, news/analyst, trade press, short-seller/activist). Agent augments with industry/company-specific sources and gives a one-line rationale per source.
→ **Gate:** approve / add / remove / edit the source set. _(This is the gate you specifically wanted before research fans out.)_

**Stage 3 — Research, Grounding & Verification**
Parallel research subagents, each scoped to an area of the coverage checklist. Every extracted fact becomes a grounded claim (source + verbatim quote + locator). Then verification runs in two layers:
- _Deterministic (script), two modes by citation type:_ (a) **tail-risk / news citations** → re-fetch the cited URL, confirm the quoted span is present, assign tier; (b) **rationale / filing citations** → locate the cited *section + figure* inside the cached filing and confirm the quoted number/text is actually there at that locator. Either way, dead/fabricated/not-found → quarantined.
- _Semantic (model):_ does the source actually *support* the claim, or is it misattributed?

Deliverables:
- **`research_brief.md`** — human-readable: exec summary → company & industry descriptions → macro & regulatory environment → findings by area. Fully cited.
- **`claims.jsonl`** — structured audit file.
- **`verification_report.md`** — pass/quarantine counts, tier distribution, coverage map (areas searched, hits, gaps).
→ **Gate:** analyst reads the brief, sees what was quarantined, steers (and may add inputs for the next stage).

**Stage 4 — Expert Analysis** _(consumes verified claims only)_
Two experts, parallel:
- _Rationale expert:_ classifies deal type and tests strategic logic **skeptically** — management's stated claim vs independent assessment, side by side — always answering *what concretely changes for the buyer* and whether **structural forces are forcing the deal or an emerging competitor is the real driver** (vs. empire-building, the brief's default suspicion). Financial rationale is **light-quant**: premium %, consideration mix, financing, accretion/dilution *sign*, stated synergies as % of premium, pro-forma leverage. Synergy credibility via break-even. Endogenous deal risks (integration, execution, financing, synergy shortfall) — the few that matter. Rationale facts cite **filing section + figure** (per the brief), not just a URL.
- _Tail-risk expert:_ researches **both target AND acquirer** (acquirer-side problems sink deals too) across the full coverage checklist — litigation & regulatory actions, antitrust, short-seller/activist reports, macro & geopolitical, consumer/product complaints, management & shareholder controversies, and financing/reputational exposure — plus the one the brief stresses most: **deterioration of the target's business fundamentals**. Wide net → **materiality filter** that scores each risk by impact-on-thesis and discards the rest. Each surviving risk carries a **transmission mechanism to *this* deal** + a tiered, verifiable source.

Output: preliminary memo, every claim tagged fact/inference and sourced.
→ **Gate:** analyst reviews the preliminary analysis and steers.

**Stage 5 — Red-Team & Finalize**
Skeptic agent attacks the experts' judgments: weak inferences, over-credulous synergy acceptance, missed counter-evidence, missed risks. May trigger **one bounded loop-back** to Stage 3 to fill a specific named gap (bounded so the run stays reproducible). Produces critique + polished `final_memo.md`.
→ **Gate:** final sign-off.

**Final outputs:** `final_memo.md` + `claims.jsonl` + `source_registry.json` (the full audit trail).

---

## 3b. Methodology grounding (how stages 2–4 know what "good" looks like)

The hard part of stages 2–4 isn't retrieval — it's analytical quality. We don't want the experts improvising "strategic logic" from scratch; we want them grounded in established M&A method. So we build a small **methodology knowledge base** (markdown method-cards the expert agents load), drawn from two sources:

**1. Anthropic's `financial-services` repo** (https://github.com/anthropics/financial-services) — directly reusable and worth studying as a pattern, not just content:
- _Method to borrow:_ `merger-model` (accretion/dilution), `competitive-analysis`, `sector-overview`, `dd-checklist` (diligence-by-workstream → maps onto our coverage checklist), `ic-memo` (memo structure).
- _Architecture to borrow:_ its managed-agent pattern is an **orchestrator + depth-1 leaf-worker subagents with "steering events" and human sign-off staging** — i.e. exactly our pipeline-with-gates. Its `check.py`/`validate.py` are deterministic lint hooks (the model for our citation verifier).
- _Note:_ many skills assume paid data connectors (FactSet, S&P, Daloopa). We'll lean on free primary sources (EDGAR, court dockets) and treat the connectors as optional upgrades.

**2. Public M&A analysis frameworks** (initial research done; to be distilled into method-cards):
- _Deal-type taxonomy_ → horizontal consolidation / vertical / capability (tech/IP) / geographic / scale — each implies a different value-creation logic and a different bear case.
- _Strategic-logic test:_ strategic synergies must translate to **measurable financial outcomes**; "creates a leading platform" with no mechanism is a red flag (matches the brief's skepticism mandate).
- _Synergy credibility via break-even:_ compute the synergy level needed to offset the premium / financing dilution. **Modest synergies needed → lower-risk deal; massive synergies needed → success hinges on execution.** This is the concrete lens for "are stated synergies large or small relative to the premium."
- _Accretion/dilution:_ sign of EPS impact given consideration mix + financing cost.

These cards are deal-agnostic (they live in the tool, not in `deal_spec`), so they help generalization rather than hurt it.

---

## 4. The evaluation pipeline (separate; runs over a finished output)

We test along **two axes**. The mapping is the key insight: **tail risk is judged on verifiability only; rationale is judged on BOTH verifiability (its factual substrate) and judgement.** No gold set — every metric below is computable from the output itself, so it's cheap to run and reproducible over the cached source snapshot.

**Axis 1 — Verifiability (objective).** _Applies to tail risk AND the facts the rationale rests on._ The core move: re-check every surfaced claim against **its own cited source** — no master answer key required (that's only what recall would need).
- _Precision (source-alignment)_ — the headline number: of all surfaced claims, the share whose cited source both exists and actually says what the claim says. We judge each claim against its own source, one at a time.
- _Fabrication rate_ — share of claims whose citation **doesn't resolve or whose quoted span is absent** (dead/invented citation). One of the two ways a claim fails the precision check; the single worst failure mode.
- _Misattribution rate_ — share of claims whose source resolves but **doesn't actually support** the claim (semantic check). The other way a claim fails.

(So fabrication + misattribution decompose *why* claims fail; precision is the top-line pass rate.)

**Axis 2 — Judgement (subjective).** _Applies to rationale only._
- _LLM-as-judge with a rubric_ — an independent model scores against fixed criteria: deal-type correctness, skepticism applied (management claim vs independent view), synergy-sizing/break-even reasoning, materiality of named risks, and fact/inference separation discipline. Rubric is versioned so scores are comparable across runs.
- _(Supporting) consistency_ — run N times and report verdict variance; a trustworthy judgement tool should be stable, not just plausible.

**Generalization:** run the whole suite on the three test deals (Paramount/WBD, Union Pacific/Norfolk Southern, Skyworks/Qorvo) and report whether quality holds or degrades.

**Output:** a scorecard table per deal + an aggregate dashboard across all four deals. Failure modes documented, not hidden.

---

## 5. Engineering scaffolding

- **Retrieval** → Claude's native web search API for open-web tail-risk sourcing, plus SEC EDGAR for filings and court-docket sources for litigation. Tier is assigned at fetch time.
- **JSON schemas** for `claim` and `source` enforce output consistency (reject malformed claims).
- **Deterministic hooks (scripts, not LLM):** citation verifier (two modes — URL resolve + filing section/figure locator), schema validator, coverage checker, fabrication scorer.
- **Content-addressed source cache** → reproducibility (and the store the filing-locator check reads from).
- **Per-stage trace logs** → inspectability.
- **Skill-packaged stages** → each stage is an invokable skill bundling its prompt + tools; the orchestrator calls them by name.
- **Config-driven generalization** → coverage checklist is a template; `deal_spec`/`run_config` carry all deal-specific input.

---

## 6. Build sequence (how to actually tackle it)

_Status legend: ✅ done · 🔄 in progress · ⬜ not started_

1. ✅ **Spine first.** Schemas + `deal_spec`/`source_registry`/`claims` + the deterministic citation verifier. Prove a fabricated URL gets caught before any agents exist. _Built in `/tool`; proof: `python scripts/run_milestone1_demo.py` quarantines fabricated, dead, and quote-absent citations. Spine smoke tests in `tests/test_spine.py`._
2. ✅ **Thin end-to-end slice on Cintas/UniFirst.** One area (target fundamentals), full loop, real data. _CC-native pipeline (skills in `.claude/skills/`) over the Python spine in `tool/`; Model C turn-by-turn gates + audit/steering log. Mock proof: `python tool/scripts/run_milestone2_mock.py`. **Live checkpoint done** (run `tool/runs/cintas_unifirst/20260607T163843Z/`): 21 verified / 0 quarantined off real SEC filings → narrative `research_brief.md` + grounded `preliminary_memo.md`. Live run surfaced + fixed: null-safe intake; SEC-compliant fetch UA + `inspect` read-path (WebFetch is 403-blocked by SEC); **Stage 2 Source Planning pulled forward** (built early); narrative brief/memo renderers (`render_brief`, `render-doc`) replacing bullet dumps._
3. ✅ **Widen research** to the full coverage checklist + verification report + gates. _Deal-agnostic 11-area `methodology/coverage_checklist.yaml`; claims carry an `area`; `coverage.py` emits `coverage_report.md` (searched/hits/gaps) — the §1 Comprehensiveness mechanism. Proven on mock (`tests/test_coverage.py`) and live: the Cintas/UF run now spans 4 areas (fundamentals/commercial/rationale/antitrust), 26 verified / 0 quarantined, with 5 gaps flagged. Stage 2 Source Planning also built here, ahead of schedule._
4. ⬜ **Add experts + materiality filter + red-team.**
5. ⬜ **Eval pipeline** + the Cintas/UF gold set; then generalize to the 3 test deals.
6. ⬜ **Harden:** failure-mode hunting, variance runs, write-up.

---

## 7. Proposed repo layout

```
/deal_spec/            # one yaml per deal (inputs only)
/methodology/          # deal-agnostic M&A method-cards for stages 2-4
/src/
  schemas/             # claim + source JSON schemas
  pipeline/            # stages 1-5
  hooks/               # deterministic verifiers/scorers
  eval/                # eval pipeline + rubric + judge
/cache/                # content-addressed fetched sources
/runs/<deal>/<ts>/     # outputs: claims, registry, briefs, memos, traces
/README.md             # how to run
```

---

## 8. Deliverables (maps to the brief's three asks)

The repo must hand in three things — the plan should produce all three, not just the tool:

1. **The tooling** — the pipeline (§3) + methodology (§3b) + scaffolding (§5), runnable on any deal via `deal_spec`.
2. **The evaluation + its outputs** — the eval pipeline (§4) plus the actual scorecards from running all four deals, failure modes included.
3. **The write-up** — how the tool works and key design decisions; the eval methodology and what it actually showed (including weaknesses); what we'd build next; and **your own independent view**: do you agree with what the tool concluded about Cintas/UniFirst on *both* rationale and tail risks, and where would you overrule it and why. _This last part is yours, not the tool's — the brief grades it specifically._

---

## 9. Decisions locked / remaining

**Locked:**
- _Retrieval_ → Claude native web search API + SEC EDGAR + court-docket sources.
- _Orchestration_ → thin master orchestrator over decoupled, file-based stages; passes pointers not contents; runs the human gates (§3).
- _Gate interaction (Model C)_ → conversational. The analyst fills in the deal_spec yaml, then executes the run via the master agent in an **agent panel**. The agent manages control flow; when an intermediate artifact is ready it informs the analyst, **blocks**, takes natural-language steering, and writes that steering back as structured file edits before proceeding. (Rejected: edit-files-and-resume CLI, blocking CLI prompts.)
- _Auditability_ → every run records a full **conversation/steering log** (the analyst's turns + the agent's), so an auditor can replay exactly what the analyst directed. This is also what reconciles Model C with reproducibility: the conversation is the UI, the recorded structured edit is the source of truth.
- _Autonomy levels_ → dropped; the human gates every stage, full stop.
- _Endogenous vs exogenous risk overlap_ → double-counting across rationale (1a) and tail-risk (1b) is acceptable; no boundary policing needed.
- _Skills_ → every stage is packaged as an invokable skill.

**Remaining to resolve during implementation:**
1. **Off-the-shelf skill vs build-our-own, per stage** — work through each stage with the analyst to decide whether an existing skill (e.g. from `financial-services`) fits or we author one together. This is an implementation activity, not a blocker.
2. **Methodology depth** — how many method-cards to write and how much to lift vs distill.
3. **Filing-locator robustness** — confirming "section + figure" citations across varied filing formats (HTML 424B3 vs PDF exhibits) is the trickiest deterministic check; needs a real test on the Cintas filing.
```
