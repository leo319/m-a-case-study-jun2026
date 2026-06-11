# Merger Analysis Tool

Turns a one-page deal spec into a sourced, audit-traceable M&A investment memo covering a deal's strategic/financial rationale and its tail risks. It is built so that an unsourced or ungrounded claim cannot structurally reach the final memo — every fact is verified against its cited source, and anything that fails is quarantined.

## Input vs. outputs

| Bucket | What | Where |
|---|---|---|
| **Input** (you edit) | The deal spec — parties, tickers, date, seed documents, analyst steering. One file per deal. Plus the deal-agnostic coverage checklist. | `deal_spec/<deal>.yaml`, `config/coverage_checklist.yaml` |
| **Intermediate artifacts** (you review at each gate) | Human-readable stage outputs: the source plan, research findings, the research brief, and the preliminary memo. | `runs/<deal>/<ts>/artifacts/` |
| **Audit trail** (full provenance) | The structured spine behind every claim: `claims.jsonl`, `source_registry.json`, the verification + coverage reports, the steering/conversation log, the cached source snapshots, and the eval scorecard. | `runs/<deal>/<ts>/audit/`, `runs/<deal>/<ts>/eval/scorecard.md`, `cache/` |
| **Final output** | The finished IC-style memo. | `runs/<deal>/<ts>/artifacts/final_memo.md` |

Everything under `runs/` and `cache/` is generated — you never hand-edit it. Editable input files carry a `# ✏️ EDITABLE INPUT` banner at the top.

## Repo layout

```
config/           deal-agnostic input knobs (coverage_checklist.yaml)          ✏️ editable
deal_spec/        one yaml per deal (cintas_unifirst.yaml is the worked example) ✏️ editable
methodology/      M&A method-cards for the expert stages
src/
  schemas/        claim + source JSON schemas — the contract everything flows through
  core/           the spine: paths, content-addressed cache, registry, claims IO, citations
  hooks/          deterministic verifiers, no LLM (validate_schema, verify_citations, check_memo)
  pipeline/       stage backends + the brief/memo renderers
  eval/           the independent evaluation pipeline + judge
scripts/          cli.py (what the skills call) + milestone proofs
tests/            fixtures + proofs
cache/            content-addressed fetched sources                            🤖 generated
runs/<deal>/<ts>/ one run, split into artifacts/ · audit/ · eval/              🤖 generated
```

The pipeline itself is driven by Claude Code skills in `../.claude/skills/` (orchestrator `merger-run` + one skill per stage), which call the Python spine here through `scripts/cli.py`.

## Getting started

```bash
pip install -r requirements.txt
```

**Step 1 — Create and fill in the deal spec.** Copy the worked example:

```bash
cp deal_spec/cintas_unifirst.yaml deal_spec/<your_deal>.yaml
```

Then edit that one file:

- **Deal identity** — acquirer/target names, tickers, and `announcement_date` (leave it `null` for a rumoured or proposed deal).
- **Seed docs** — the sources intake should fetch first (the merger proxy/424B3, both companies' latest 10-Ks, the deal press release — real, stable URLs only).
- **Seed terms** *(optional)* — hunches like price, premium, synergies. Seeds only; never treated as fact until grounded in a cited source.
- **Steering** *(optional)* — your priorities under `run_config.steering` (e.g. "focus on antitrust").

**Step 2 — Run the pipeline.** In Claude Code, invoke the orchestrator skill on your spec:

```
/merger-run deal_spec/<your_deal>.yaml
```

It runs the five stages — intake → source planning → research → expert → red-team & finalize — and **stops at a human gate after each one**, presenting that stage's artifact for you to approve, edit, or steer before it proceeds. The final memo lands in `runs/<your_deal>/<ts>/artifacts/final_memo.md`.

**Step 3 — (Optional) Evaluate.** Run the independent evaluator over a finished run to get the scorecard (fact precision, fabrication/misattribution rates, inference validity, coverage, utilization):

```
/eval runs/<your_deal>/<ts>
```

---

_The Python spine is also callable directly — `python scripts/cli.py map` prints the full pipeline, and `python scripts/run_milestone2_mock.py` proves the whole loop with no tokens (fixtures stand in for the agents)._
