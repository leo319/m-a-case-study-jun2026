# Merger Analysis Tool

**Turn a one-page deal spec into a sourced, fact-checked M&A investment memo.**

It analyzes a merger along two dimensions — the deal's strategic & financial rationale and the tail risks that could derail it — and is built so that an unsourced or ungrounded claim cannot structurally reach the final memo: every fact is verified against its cited source, and anything that fails is quarantined.

## Input vs. outputs

| Bucket | What | Where |
|---|---|---|
| **Deal-specific input** (you edit, one per deal) | The deal spec — parties, tickers, date, seed documents, analyst steering. | `deal_spec/<deal>.yaml` |
| **Deal-agnostic data knobs** (you edit, shared across deals) | What research must cover (areas, subtopics, canonical sources) and the source taxonomy (classes, tiers, method-card buckets). | `config/coverage_checklist.yaml`, `config/source_classes.yaml`, `/methodology` |
| **Intermediate artifacts** (you review at each gate) | Human-readable stage outputs: the source plan, research findings, the research brief, and the preliminary memo. | `runs/<deal>/<ts>/artifacts/` |
| **Audit trail** (full provenance) | The structured spine behind every claim: `claims.jsonl`, `source_registry.json`, the verification + coverage reports, the steering/conversation log, the cached source snapshots, and the eval scorecard. | `runs/<deal>/<ts>/audit/`, `runs/<deal>/<ts>/eval/scorecard.md`, `cache/` |
| **Final output** | The finished IC-style memo. | `runs/<deal>/<ts>/artifacts/final_memo.md` |

Everything under `runs/` and `cache/` is generated — you never hand-edit it. Editable input files carry a `# ✏️ EDITABLE INPUT` banner at the top.

## Repo layout

```
config/            deal-agnostic data knobs — coverage_checklist.yaml, source_classes.yaml   ✏️ editable
deal_spec/         one YAML per deal (cintas_unifirst.yaml is the worked example)            ✏️ editable
methodology/       deal-agnostic M&A method cards (00–05) the plan/expert stages reason from ✏️ editable
src/
  schemas/         claim + source JSON schemas — the contract every claim flows through
  core/            the spine: paths, content-addressed cache, source registry, claims IO, citations
  hooks/           deterministic checks, no LLM (schema validation, citation verification, memo guard)
  pipeline/        stage backends (intake, source-plan, research, expert, coverage) + brief/memo renderers
  eval/            the standalone evaluation harness + claim-verifier judge
scripts/           cli.py — the single entrypoint the skills call
tests/             zero-token tests + fixtures
requirements.txt   Python dependencies
cache/             content-addressed snapshots of fetched sources               🤖 generated
runs/<deal>/<ts>/  one run — artifacts/ (review) · audit/ (provenance) · eval/   🤖 generated
```

The pipeline is driven by Claude Code skills in `../.claude/skills/` (the `merger-run` orchestrator + one skill per stage), which call this Python spine through `scripts/cli.py`.

## Getting started

**Prerequisites:** Python 3.10+ and Claude Code (the pipeline runs as Claude Code skills). Then install the Python dependencies:

```bash
pip install -r requirements.txt
```

**1 — Create the deal spec.** Copy the worked example and edit that one file:

```bash
cp deal_spec/cintas_unifirst.yaml deal_spec/<your_deal>.yaml
```

- **Deal identity** — acquirer/target names, tickers, and `announcement_date` (`null` for a rumoured or proposed deal).
- **Seed docs** — where intake starts: the merger proxy / 424B3, both companies' latest 10-Ks, the deal press release (real, stable URLs only).
- **Seed terms** *(optional)* — hunches like price, premium or synergies; treated as leads, never as fact until grounded in a cited source.
- **Steering** *(optional)* — your priorities under `run_config.steering` (e.g. "focus on antitrust").

**2 — Run the pipeline.** In Claude Code:

```
/merger-run deal_spec/<your_deal>.yaml
```

It runs five stages — intake → source planning → research → expert → red-team & finalize — and **stops at a human gate after each**, presenting that stage's artifact for you to approve, edit, or steer. The final memo lands in `runs/<your_deal>/<ts>/artifacts/final_memo.md`.

**3 — Evaluate (optional).** Independently re-verify a finished run and produce a scorecard — fact precision, fabrication / misattribution rates, inference validity, coverage and utilization:

```
/eval runs/<your_deal>/<ts>
```

---

_The Python spine is also callable directly — `python scripts/cli.py map` prints the full pipeline, and `python scripts/run_milestone2_mock.py` proves the whole loop with no tokens (fixtures stand in for the agents)._
