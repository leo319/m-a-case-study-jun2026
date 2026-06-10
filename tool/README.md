# Merger Analysis Tool

A pipeline that turns a deal specification into a sourced, audit-traceable M&A memo,
designed so that **an unsourced or ungrounded claim cannot structurally reach the
final memo** (see [`../PLAN.md`](../PLAN.md)).

> Status: **Milestones 1–3 done; pipeline hardened.** Spine + full gated pipeline
> (intake → source planning → research → expert → memo), Model C human gates, coverage
> checklist/map. Proven live on Cintas/UniFirst: **9 of 11 areas, 100 verified claims,
> 0 required/recommended gaps** — with page-level decimal citations, an auto
> "sources consulted" appendix, and Stage-2 deal-wide source planning + discovery.

## Inputs vs. outputs (what you can edit)

Three unmistakable buckets:

| Bucket | Where | Edit? |
|---|---|---|
| ✏️ **Deal-specific inputs** | `deal_spec/<deal>.yaml` | yes — one file per deal (copy the worked example) |
| ✏️ **Deal-agnostic inputs** (tool-wide knobs) | `config/` | yes — e.g. `coverage_checklist.yaml` (what research must cover) |
| 🤖 **Generated outputs** | `runs/`, `cache/` | no — produced by the tool (gitignored) |

Editable input files carry a `# ✏️ EDITABLE INPUT · scope: …` banner at the top.

## Layout

```
config/           deal-agnostic input knobs (coverage_checklist.yaml)        ✏️ editable
deal_spec/        one yaml per deal (cintas_unifirst.yaml is the example)     ✏️ editable
methodology/      M&A method-cards for stages 2-4 (future: M3b/4)
src/
  schemas/        claim + source JSON schemas — the contract everything flows through
  core/           the spine: paths, content-addressed cache, registry, claims IO, schema, fetch,
                  citations (page-level footnote builder shared by the brief & memo renderers)
  hooks/          deterministic verifiers (no LLM): validate_schema, verify_citations, check_memo
  pipeline/       stages + backends (intake, source_plan, ingest_research, coverage, render_*, ...)
  eval/           eval pipeline + rubric + judge                  (Milestone 5)
cache/            content-addressed fetched sources (gitignored)             🤖 generated
runs/<deal>/<YYYY-MM-DD HHMM>/   one run (Pacific-time folder), split into:   🤖 generated
    artifacts/      what the analyst reviews: research_brief.md, preliminary_memo.md,
                    research_findings.md, source_plan.md
    audit/          full trail: claims.jsonl, source_registry.json, *_report.md,
                    steering_log.md, conversation.jsonl, intake/specs/proposals
scripts/          runnable entry points (cli.py + milestone proofs)
tests/            fixtures + proofs
```

## The data model (PLAN.md §2)

- **`deal_spec/*.yaml`** — all deal-specific input. Nothing company-specific lives in code.
- **`source_registry.json`** — every source: `{id, title, url, tier, retrieved_at, content_hash, local_path}`.
- **`claims.jsonl`** — the audit spine. Each claim is `fact` (needs source + verbatim
  quote) or `inference` (needs the verified claims it builds on), and carries a
  `status` of `verified | quarantined | unverified` set by the verifier.

Source tiers travel with every claim: **T1** primary (SEC/court/regulator) > **T2**
reputable secondary > **T3** trade/specialist > **T4** unverified.

## Setup

```bash
pip install -r requirements.txt
```

## Run the Milestone 1 proof

Shows that fabricated, dead, and quote-absent citations are quarantined by code —
deterministically, with no network and no model:

```bash
python scripts/run_milestone1_demo.py
```

## Run the pipeline (Milestone 2)

CC-native: the pipeline is driven by skills in `../.claude/skills/` (orchestrator
`merger-run` + stage skills), which call the Python spine via one CLI. The analyst
invokes `/merger-run` in Claude Code; the orchestrator shows the full pipeline, then
runs each stage and stops at a human gate (Model C). Every gate is recorded to an
audit/steering log for reproducibility.

Prove the whole loop with **no tokens** (fixtures stand in for the agents):

```bash
python scripts/run_milestone2_mock.py
```

The pipeline CLI (what the skills call):

```bash
python scripts/cli.py map                                  # show the full pipeline
python scripts/cli.py intake   --deal deal_spec/<deal>.yaml
python scripts/cli.py research --run RUNDIR --proposals proposals.json
python scripts/cli.py expert   --run RUNDIR --memo memo_spec.json
python scripts/cli.py render   --run RUNDIR --memo memo_spec.json   # fail-closed
python scripts/cli.py gate     --run RUNDIR --stage research --presented "..." --steering "..."
```

## The deterministic hooks

```bash
# validate every claim/source against the JSON schemas (exit 1 if any malformed)
python -m src.hooks.validate_schema --run runs/<deal>/<ts>

# verify citations: set each claim verified/quarantined, write verification_report.md
python -m src.hooks.verify_citations --run runs/<deal>/<ts>
```

## Evaluation

Two eval types, split by a single fact: **precision and recall have very different
costs.** Precision is self-contained — "is each surfaced claim supported by its own
source?" is answerable one claim at a time, no answer key. Recall is not — "did we
catch everything we should have?" is unanswerable without knowing the universe of
what *should* have been found, which needs a gold set. So precision runs live today;
recall is future work.

### Eval #2 — live independent verification (built)

A **separate code path** from the in-pipeline deterministic verifier, so it doesn't
inherit its blind spots: it re-checks every claim the final memo **surfaces**, judging
each against its **own cached source** (not the memo narrative). That lets it catch
what the deterministic verifier structurally cannot — **semantic misattribution**: a
real, live quote cited for a statement it doesn't actually support.

Fan-out workflow: surfaced claims are chunked (~10 per subagent), one `claim-verifier`
runs per chunk in parallel, then results aggregate into a single scorecard (summary table
+ per-claim ledger) under `run/eval/`. Standalone — invoke the `eval` skill on any finished
run; it is **not** part of the gated `merger-run` pipeline.

Per-claim verdicts:

| Claim type | Verdicts |
|---|---|
| **Fact** | PASS / FABRICATION (citation dead or quote absent) / MISATTRIBUTION (quote present, statement overreaches it) |
| **Inference** | PASS / WEAK-INFERENCE (conclusion doesn't follow) / DISCIPLINE (opinion-as-fact, or broken fact/inference separation) |

Headline metrics: **fact precision, fabrication rate, misattribution rate,
inference-validity rate, separation-discipline rate.** Plus two **recall proxies**
reused from the coverage stage — coverage completeness (breadth of areas with a
verified claim) and utilization (did the memo use the verified inferences it gathered).
Be explicit: these measure *"did we use what we found,"* **not** *"did we find what
exists."*

Output under `run/eval/`: `manifest.json`, `chunks/`, `scorecard.md` (a summary table —
metric · definition · score · what-failed — followed by the full per-claim ledger, failures
on top) + `scorecard.json`; cross-deal roll-up at `runs/_eval_dashboard.md`. Everything reads
the cached source snapshot, so a re-run is deterministic and a regression is attributable to
the tool, not a changed source.

```bash
eval-plan      --run RUNDIR [--chunk-size 10]   # chunk surfaced claims, write manifest
eval-source    --run RUNDIR --claim ID          # re-check one claim vs. its cached source
eval-aggregate --run RUNDIR                      # scorecard.md (summary + ledger) + json
eval-dashboard                                   # cross-deal roll-up
```

Skill: invoke `eval` on a run.

### Eval #1 — gold-set recall (designed, future)

Precision is self-contained and already covered by eval #2. **Recall is not** — it
requires a **gold set** of trusted past memos to define what should have been found.
Eval #2's coverage/utilization proxies are a partial floor, not a substitute. What
eval #1 adds, and only it can — **true recall**:

- **Fact recall** — of the facts a human analyst judged material in the gold memo, what
  fraction did the tool surface? (a dropped geography fact, a missing precedent deal, an
  unmentioned material weakness).
- **Insight/judgment recall** (the higher-value one) — did the tool independently reach
  the gold memo's key judgments: overpayment, integration risk, antitrust as the binding
  constraint? Missing a fact is a blemish; missing the thesis is a failure.
- **Precision vs. a canonical value** — for numeric claims, compare to the known-correct
  figure (e.g. the premium really is 102.5%), not just "internally supported."

**How it's used:** a pinned **regression harness** — run on every model upgrade, prompt
change, or pipeline tweak; track precision *and* recall deltas; alarm on regression.

**Reliability (run-to-run stability).** The pipeline's LLM stages (research, expert,
red-team) are non-deterministic, so the *same* deal run twice can surface different
claims and reach different judgments — a single eval score is one sample, not the tool's
true quality. Reliability runs the **whole pipeline N times** (e.g. 3) on one deal, evals
each run, and reports the **spread** — mean ± range (or stdev) — of every metric:
precision, fabrication, misattribution, inference validity, separation discipline,
coverage, utilization, and, with the gold set, **fact recall and insight recall**. It
lives in eval #1 because recall is the metric most exposed to run-to-run luck (did *this*
run happen to find the material facts and the thesis?), and recall only exists against the
gold set — precision/coverage stability can ride on eval #2 across the N runs, but the
full picture needs the gold set. The point is to tell **dependable quality from luck**: a
high mean with high variance is untrustworthy, so alarm on the *spread*, not just the
level. In the harness, each pinned deal becomes N runs, tracking both the level and the
stability of every metric on each change.

**How the gold set is built** (why it's future labor): hand-curate a handful of
**closed** deals where both the real merger proxy *and* a real sell-side/IC memo exist;
annotate the material facts and key judgments; version it. The cost is the annotation.

**The honest caveat:** a gold memo encodes one analyst's choices, so recall against it
measures alignment to that analyst, not absolute truth — a "miss" may be a legitimate
difference of emphasis. Mitigate with multiple annotators / a consensus material-fact +
key-judgment list; treat recall as directional.

### Summary

| Claim type | What's checked | Needs gold set? | Eval |
|---|---|---|---|
| **Fact** | source-alignment: citation resolves, quote present, statement entailed | No | #2 live |
| **Rationale inference** | supports resolve + reasoning follows + fact/inference separation | No | #2 live |
| **What was missed** | recall vs. material facts / key judgments | Yes | #1 future |
| **Run-to-run reliability** | spread of every metric across N full pipeline re-runs | Yes (for recall) | #1 future |
