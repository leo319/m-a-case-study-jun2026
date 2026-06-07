# Merger Analysis Tool

A pipeline that turns a deal specification into a sourced, audit-traceable M&A memo,
designed so that **an unsourced or ungrounded claim cannot structurally reach the
final memo** (see [`../PLAN.md`](../PLAN.md)).

> Status: **Milestone 1 (the spine) — built.** Schemas, the data model, the
> content-addressed cache, and the deterministic citation verifier exist and are
> proven. No agents yet.

## Layout (PLAN.md §7)

```
deal_spec/        one yaml per deal (inputs only) — cintas_unifirst.yaml is the worked example
methodology/      deal-agnostic M&A method-cards for stages 2-4   (Milestone 3b/4)
src/
  schemas/        claim + source JSON schemas — the contract everything flows through
  core/           the spine: paths, content-addressed cache, registry, claims IO, schema, fetch
  hooks/          deterministic verifiers/scorers (no LLM): validate_schema, verify_citations
  pipeline/       stages 1-5                                       (Milestone 2+)
  eval/           eval pipeline + rubric + judge                  (Milestone 5)
cache/            content-addressed fetched sources (gitignored)
runs/<deal>/<ts>/ outputs: claims, registry, briefs, memos, traces (gitignored)
scripts/          runnable entry points
tests/            fixtures + proofs
```

> Note: `src/core/` is a small addition to the §7 sketch — shared spine code the
> hooks and (later) stages import, kept separate from the deterministic `hooks/`.

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

## The deterministic hooks

```bash
# validate every claim/source against the JSON schemas (exit 1 if any malformed)
python -m src.hooks.validate_schema --run runs/<deal>/<ts>

# verify citations: set each claim verified/quarantined, write verification_report.md
python -m src.hooks.verify_citations --run runs/<deal>/<ts>
```
