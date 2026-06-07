# Merger Analysis Tool

A pipeline that turns a deal specification into a sourced, audit-traceable M&A memo,
designed so that **an unsourced or ungrounded claim cannot structurally reach the
final memo** (see [`../PLAN.md`](../PLAN.md)).

> Status: **Milestones 1–3 done.** Spine + full gated pipeline (intake → source
> planning → research → expert → memo), Model C human gates, coverage checklist/map.
> Proven live on Cintas/UniFirst (target fundamentals + antitrust).

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
  core/           the spine: paths, content-addressed cache, registry, claims IO, schema, fetch
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
