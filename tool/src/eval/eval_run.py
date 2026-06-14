"""Live independent verification eval (eval #2) — plan / source-dossier / aggregate / dashboard.

The pipeline's own verifier (src/hooks/verify_citations.py) is a deterministic
substring check run *inside* the pipeline. This eval is the independent, after-the-fact
audit: it asks an outside verifier to re-judge every claim the memo actually surfaced,
each against its OWN cached source — catching the semantic failures the substring check
can't see (a quote present but misattributed; an inference that overreaches its supports).

Flow (the `eval` skill drives this; nothing here calls an LLM directly):
  1. plan(run_dir)            -> run/eval/chunks/chunk_NN.json + run/eval/manifest.json
  2. source_dossier(...)      -> a self-contained, per-claim brief the verifier reads
  3. (verifier subagents)     -> run/eval/chunks/chunk_NN_result.json
  4. aggregate(run_dir)       -> run/eval/{scorecard.md (summary + ledger), scorecard.json}
  5. dashboard(runs_root)     -> runs_root/_eval_dashboard.md

Everything is judged against the cached source snapshot, so a run re-evaluates
identically — the eval is reproducible.

CLI (via tool/scripts/cli.py):
  python tool/scripts/cli.py eval-plan      --run RUNDIR [--chunk-size 10]
  python tool/scripts/cli.py eval-source    --run RUNDIR --claim ID [--full]
  python tool/scripts/cli.py eval-aggregate --run RUNDIR
  python tool/scripts/cli.py eval-dashboard [--runs-root tool/runs]
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from ..core import cache
from ..core import claims as claims_io
from ..core import registry as registry_io
from ..core import textutil
from ..core.paths import audit_dir, claims_path, registry_path, run_context
from ..pipeline import coverage

VERIFIER_MODEL = "opus-4-8"

# Same citation-token grammar the renderer / coverage utilization use.
_CITE_TOKEN = re.compile(r"\[\[([A-Za-z0-9_]+)\]\]")

# Context window (chars) shown around a located quote in a claim dossier.
_CONTEXT_RADIUS = 600
# How much leading text to show when the quote is NOT found (for confirmation).
_ABSENT_PREVIEW = 800

# Verdict vocabularies (the verifier writes these; we consume them).
FACT_VERDICTS = ("PASS", "FABRICATION", "MISATTRIBUTION")
INFERENCE_VERDICTS = ("PASS", "WEAK-INFERENCE", "DISCIPLINE")
# Failures-first ordering for the ledger.
_LEDGER_ORDER = ["FABRICATION", "MISATTRIBUTION", "WEAK-INFERENCE", "DISCIPLINE", "PASS"]


# --- paths -------------------------------------------------------------------

def eval_dir(run_dir: str | Path) -> Path:
    return Path(run_dir) / "eval"


def chunks_dir(run_dir: str | Path) -> Path:
    return eval_dir(run_dir) / "chunks"


def _deal_name(run_dir: str | Path) -> str:
    """Deal = the run dir's grandparent name (runs/<deal>/<ts>)."""
    return Path(run_dir).resolve().parent.name


def _run_name(run_dir: str | Path) -> str:
    return Path(run_dir).resolve().name


# --- memo-spec surfaced claims ----------------------------------------------

def _memo_spec_path(run_dir: str | Path) -> Path:
    """Prefer the final memo spec; fall back to the preliminary memo spec."""
    final = audit_dir(run_dir) / "final_memo_spec.json"
    return final if final.exists() else audit_dir(run_dir) / "memo_spec.json"


def _load_memo_spec(run_dir: str | Path) -> tuple[dict, Path]:
    path = _memo_spec_path(run_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"no memo spec found (looked for final_memo_spec.json / memo_spec.json in "
            f"{audit_dir(run_dir)})"
        )
    return json.loads(path.read_text(encoding="utf-8")), path


def surfaced_claim_ids(memo_spec: dict) -> list[str]:
    """Claim ids cited via [[id]] tokens in the memo spec's section bodies, in
    first-appearance order (deduped)."""
    seen: list[str] = []
    out: set[str] = set()
    for sec in memo_spec.get("sections", []):
        for cid in _CITE_TOKEN.findall(sec.get("body", "")):
            if cid not in out:
                out.add(cid)
                seen.append(cid)
    return seen


# --- plan --------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def plan(run_dir: str | Path, chunk_size: int = 10) -> dict:
    """Read surfaced claim ids, resolve to full claim records, split into chunks.

    Writes run/eval/chunks/chunk_NN.json and run/eval/manifest.json. Returns the
    manifest dict.
    """
    run_dir = Path(run_dir)
    memo_spec, spec_path = _load_memo_spec(run_dir)
    ids = surfaced_claim_ids(memo_spec)

    by_id = claims_io.index_by_id(claims_io.load_claims(claims_path(run_dir)))
    records: list[dict] = []
    missing: list[str] = []
    for cid in ids:
        rec = by_id.get(cid)
        if rec is None:
            missing.append(cid)
        else:
            records.append(rec)

    n_facts = sum(1 for r in records if r.get("type") == "fact")
    n_inferences = sum(1 for r in records if r.get("type") == "inference")

    cdir = chunks_dir(run_dir)
    cdir.mkdir(parents=True, exist_ok=True)
    # Clear any stale chunk/result files from a prior plan so aggregate is clean.
    for stale in cdir.glob("chunk_*.json"):
        stale.unlink()

    chunk_meta: list[dict] = []
    n_chunks = math.ceil(len(records) / chunk_size) if records else 0
    for n in range(n_chunks):
        batch = records[n * chunk_size:(n + 1) * chunk_size]
        fname = f"chunk_{n:02d}.json"
        (cdir / fname).write_text(
            json.dumps({"chunk": n, "claims": batch}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        chunk_meta.append({
            "chunk": n,
            "file": f"eval/chunks/{fname}",
            "result_file": f"eval/chunks/chunk_{n:02d}_result.json",
            "n_claims": len(batch),
            "claim_ids": [r["id"] for r in batch],
        })

    manifest = {
        "deal": _deal_name(run_dir),
        "run": _run_name(run_dir),
        "generated_from": spec_path.name,
        "total_surfaced": len(records),
        "facts": n_facts,
        "inferences": n_inferences,
        "chunk_size": chunk_size,
        "n_chunks": n_chunks,
        "missing_surfaced_ids": missing,
        "snapshot": {
            "claims_sha256": _sha256_file(claims_path(run_dir)),
            "registry_sha256": _sha256_file(registry_path(run_dir)),
        },
        "verifier_model": VERIFIER_MODEL,
        "chunks": chunk_meta,
    }
    (eval_dir(run_dir) / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


# --- per-claim source dossier ------------------------------------------------

def _source_text(content_hash: str, media_type: str | None, cache_dir: Path) -> str:
    """Normalized cached source text (the same view the deterministic verifier sees)."""
    return textutil.normalize(
        textutil.to_text(cache.load(cache_dir, content_hash), media_type)
    )


def source_dossier(run_dir: str | Path, claim_id: str, full: bool = False) -> str:
    """A self-contained dossier the verifier reads to judge ONE claim independently.

    For a fact: each cited source's registry record, the deterministic quote_present
    bool, and either a ±600-char context window around the quote (present) or the
    first 800 chars (absent) so the verifier can confirm for itself. full=True dumps
    the entire normalized source text instead of a window.

    For an inference: each support's statement / type / status, so the verifier can
    check the conclusion actually follows from verified supports.
    """
    run_dir = Path(run_dir)
    # Same cache the deterministic verifier reads from (the shared /cache root).
    cache_dir = run_context(run_dir).cache_dir
    claims = claims_io.load_claims(claims_path(run_dir))
    by_id = claims_io.index_by_id(claims)
    sources = registry_io.load_registry(registry_path(run_dir))

    claim = by_id.get(claim_id)
    if claim is None:
        return f"CLAIM '{claim_id}' NOT FOUND in {claims_path(run_dir)}"

    out: list[str] = []
    out.append("=" * 78)
    out.append(f"CLAIM {claim['id']}  [{claim.get('type', '?')} / {claim.get('module', '?')}]"
               f"  status={claim.get('status', '?')}")
    out.append("=" * 78)
    out.append(f"statement: {claim.get('statement', '')}")
    if claim.get("locator"):
        out.append(f"locator:   {claim.get('locator')}")
    if claim.get("area"):
        out.append(f"area:      {claim.get('area')}")
    out.append("")

    if claim.get("type") == "fact":
        out.extend(_fact_dossier(claim, sources, cache_dir, full))
    elif claim.get("type") == "inference":
        out.extend(_inference_dossier(claim, by_id))
    else:
        out.append(f"(unknown claim type {claim.get('type')!r} — nothing to ground)")

    return "\n".join(out)


def _fact_dossier(claim: dict, sources: dict[str, dict], cache_dir: Path,
                  full: bool) -> list[str]:
    out: list[str] = []
    quote = claim.get("quote", "")
    out.append(f"QUOTE (verbatim, as the pipeline recorded it):\n  «{quote}»")
    out.append("")
    source_ids = claim.get("source_ids", [])
    if not source_ids:
        out.append("NO source_ids ON THIS FACT — nothing to ground it against.")
        return out

    for sid in source_ids:
        out.append("-" * 78)
        src = sources.get(sid)
        if src is None:
            out.append(f"SOURCE {sid}: NOT IN REGISTRY (dead or fabricated citation).")
            continue
        out.append(f"SOURCE {sid}")
        out.append(f"  title: {src.get('title', '(no title)')}")
        out.append(f"  url:   {src.get('url', '(no url)')}")
        out.append(f"  tier:  {src.get('tier', '?')}    media: {src.get('media_type', '?')}")

        content_hash = src.get("content_hash")
        if not content_hash or not src.get("local_path"):
            out.append("  cached: NO (never fetched) — cannot ground the quote.")
            continue
        if not cache.verify_integrity(cache_dir, content_hash):
            out.append("  cached: FAILED INTEGRITY CHECK (missing or tampered).")
            continue

        text = _source_text(content_hash, src.get("media_type"), cache_dir)
        present = textutil.quote_present(quote, text)
        out.append(f"  cached source length (normalized): {len(text)} chars")
        out.append(f"  quote_present(deterministic substring check): {present}")

        if full:
            out.append("  --- FULL NORMALIZED SOURCE TEXT ---")
            out.append(text)
            out.append("  --- END SOURCE TEXT ---")
            continue

        if present:
            # `text` is already normalized and `present` was computed with the same
            # normalization, so the quote is guaranteed findable here (guard idx >= 0
            # defensively in case that ever changes).
            nq = textutil.normalize(quote)
            idx = max(text.find(nq), 0)
            start = max(0, idx - _CONTEXT_RADIUS)
            end = min(len(text), idx + len(nq) + _CONTEXT_RADIUS)
            out.append(f"  --- CONTEXT WINDOW (±{_CONTEXT_RADIUS} chars around the quote) ---")
            out.append(("…" if start > 0 else "") + text[start:end] + ("…" if end < len(text) else ""))
            out.append("  --- END CONTEXT ---")
        else:
            out.append("  *** QUOTE NOT FOUND IN SOURCE ***")
            out.append(f"  --- FIRST {_ABSENT_PREVIEW} CHARS (so you can confirm) ---")
            out.append(text[:_ABSENT_PREVIEW] + ("…" if len(text) > _ABSENT_PREVIEW else ""))
            out.append("  --- END PREVIEW ---")
    return out


def _inference_dossier(claim: dict, by_id: dict[str, dict]) -> list[str]:
    out: list[str] = []
    supports = claim.get("supports", [])
    out.append("This is an INFERENCE. Judge whether the conclusion follows from its supports,")
    out.append("and whether each support is itself a grounded/verified claim.")
    out.append("")
    if not supports:
        out.append("NO supports listed — an inference with nothing under it is ungrounded.")
        return out
    for sid in supports:
        out.append("-" * 78)
        sup = by_id.get(sid)
        if sup is None:
            out.append(f"SUPPORT {sid}: DOES NOT EXIST in claims.jsonl.")
            continue
        out.append(f"SUPPORT {sid}  [{sup.get('type', '?')}]  status={sup.get('status', '?')}")
        out.append(f"  statement: {sup.get('statement', '')}")
    return out


# --- aggregate ---------------------------------------------------------------

def _load_results(run_dir: str | Path) -> list[dict]:
    cdir = chunks_dir(run_dir)
    verdicts: list[dict] = []
    for rf in sorted(cdir.glob("chunk_*_result.json")):
        data = json.loads(rf.read_text(encoding="utf-8"))
        for v in data.get("verdicts", []):
            verdicts.append(v)
    return verdicts


def _rate(num: int, den: int) -> float | str:
    return round(num / den, 4) if den else "n/a"


def _pct(rate: float | str) -> str:
    return f"{rate * 100:.1f}%" if isinstance(rate, (int, float)) else "n/a"


def aggregate(run_dir: str | Path) -> dict:
    """Read chunk_*_result.json, build verdict rows, compute metrics, and write
    eval/{scorecard.md (summary + ledger), scorecard.json}. Returns the scorecard dict."""
    run_dir = Path(run_dir)
    manifest_path = eval_dir(run_dir) / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    surfaced_ids: list[str] = []
    for ch in manifest.get("chunks", []):
        surfaced_ids.extend(ch.get("claim_ids", []))

    verdicts = _load_results(run_dir)
    by_claim = {v["claim_id"]: v for v in verdicts}

    # Surfaced claims that received no verdict.
    unjudged = [cid for cid in surfaced_ids if cid not in by_claim]

    fact_v = [v for v in verdicts if v.get("type") == "fact"]
    inf_v = [v for v in verdicts if v.get("type") == "inference"]

    facts_total = len(fact_v)
    facts_pass = sum(1 for v in fact_v if v.get("verdict") == "PASS")
    facts_fab = sum(1 for v in fact_v if v.get("verdict") == "FABRICATION")
    facts_mis = sum(1 for v in fact_v if v.get("verdict") == "MISATTRIBUTION")

    inf_total = len(inf_v)
    inf_pass = sum(1 for v in inf_v if v.get("verdict") == "PASS")
    inf_discipline = sum(1 for v in inf_v if v.get("verdict") == "DISCIPLINE")

    metrics = {
        "fact_precision": _rate(facts_pass, facts_total),
        "fabrication_rate": _rate(facts_fab, facts_total),
        "misattribution_rate": _rate(facts_mis, facts_total),
        "inference_validity_rate": _rate(inf_pass, inf_total),
        "separation_discipline_rate": _rate(inf_total - inf_discipline, inf_total),
    }

    # Coverage + utilization, reusing the pipeline's own helpers.
    cmap = coverage.coverage_map(run_dir)
    coverage_pct = _rate(cmap["areas_covered"], cmap["total_areas"])
    memo_spec, _ = _load_memo_spec(run_dir)
    util = coverage.utilization(run_dir, memo_spec)
    cited = sum(d["cited"] for d in util["by_module"].values())
    util_total = sum(d["total"] for d in util["by_module"].values())
    utilization_rate = _rate(cited, util_total)

    scorecard = {
        "deal": manifest.get("deal", _deal_name(run_dir)),
        "run": manifest.get("run", _run_name(run_dir)),
        "surfaced": len(surfaced_ids),
        "judged": len(verdicts),
        "unjudged_surfaced_ids": unjudged,
        "facts_total": facts_total,
        "facts_pass": facts_pass,
        "facts_fabrication": facts_fab,
        "facts_misattribution": facts_mis,
        "inferences_total": inf_total,
        "inferences_pass": inf_pass,
        "inferences_discipline": inf_discipline,
        **metrics,
        "coverage_pct": coverage_pct,
        "areas_covered": cmap["areas_covered"],
        "total_areas": cmap["total_areas"],
        "utilization": utilization_rate,
        "utilization_cited": cited,
        "utilization_total": util_total,
        # Gold-set-only metric: did we surface the material facts and reach the key
        # judgments? Computed only when a gold set is supplied; "n/a" otherwise.
        "fact_insight_recall": "n/a",
        "verifier_model": manifest.get("verifier_model", VERIFIER_MODEL),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    uncovered = [r["title"] for r in cmap["rows"] if r["hits"] == 0]
    _write_report(run_dir, scorecard, verdicts, unjudged, uncovered,
                  len(util["unused_inference"]))
    (eval_dir(run_dir) / "scorecard.json").write_text(
        json.dumps(scorecard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # The old two-file layout is now one report; drop a stale ledger if present.
    (eval_dir(run_dir) / "ledger.md").unlink(missing_ok=True)
    return scorecard


def _ledger_sort_key(v: dict) -> tuple[int, str]:
    verdict = v.get("verdict", "PASS")
    try:
        rank = _LEDGER_ORDER.index(verdict)
    except ValueError:
        rank = len(_LEDGER_ORDER)  # unknown verdicts sink to the bottom
    return rank, v.get("claim_id", "")


def _md_cell(text: str) -> str:
    """Make a string safe for a single markdown table cell."""
    return (text or "").replace("|", "\\|").replace("\n", " ").strip() or "—"


def _write_report(run_dir: str | Path, sc: dict, verdicts: list[dict],
                  unjudged: list[str], uncovered_areas: list[str],
                  unused_inferences: int) -> Path:
    """Write the single human-facing eval file: a summary table up top
    (metric · definition · score · what failed), the full per-claim ledger below."""
    def _fails(verdict: str) -> str:
        ids = [v.get("claim_id", "") for v in verdicts if v.get("verdict") == verdict]
        return ", ".join(ids) if ids else "—"

    fact_fail = [v.get("claim_id", "") for v in verdicts
                 if v.get("type") == "fact" and v.get("verdict") != "PASS"]
    cov_note = ", ".join(uncovered_areas) if uncovered_areas else "—"
    util_note = (f"{unused_inferences} verified research inference(s) unused"
                 if unused_inferences else "—")

    lines = [
        f"# Eval report — {sc['deal']} / {sc['run']}",
        "",
        f"_Independent verification of the **{sc['surfaced']}** claims the memo surfaced "
        f"({sc['facts_total']} facts, {sc['inferences_total']} inferences), judged against the "
        f"cached source snapshot by `{sc['verifier_model']}`._",
        "",
        "## Summary",
        "",
        "| Tier | Metric | What it asks | Score | What failed |",
        "|---|---|---|---|---|",
        f"| **Primary** | **Precision** | Does the citation resolve, is the quote present, and "
        f"does it actually support the statement? | {_pct(sc['fact_precision'])} "
        f"({sc['facts_pass']}/{sc['facts_total']}) "
        f"| {_md_cell(', '.join(fact_fail) if fact_fail else '—')} |",
        f"| | &nbsp;&nbsp;↳ Fabrication rate | Citation dead or absent. "
        f"| {_pct(sc['fabrication_rate'])} ({sc['facts_fabrication']}/{sc['facts_total']}) "
        f"| {_md_cell(_fails('FABRICATION'))} |",
        f"| | &nbsp;&nbsp;↳ Misattribution rate | Resolves and quoted correctly, but doesn't "
        f"support the statement. | {_pct(sc['misattribution_rate'])} "
        f"({sc['facts_misattribution']}/{sc['facts_total']}) | {_md_cell(_fails('MISATTRIBUTION'))} |",
        f"| | **Inference validity** (entailment) | Are the supports verified, and does the "
        f"conclusion follow? | {_pct(sc['inference_validity_rate'])} "
        f"({sc['inferences_pass']}/{sc['inferences_total']}) | {_md_cell(_fails('WEAK-INFERENCE'))} |",
        f"| **Secondary** | Separation discipline | No opinion dressed up as fact. "
        f"| {_pct(sc['separation_discipline_rate'])} "
        f"({sc['inferences_total'] - sc['inferences_discipline']}/{sc['inferences_total']}) "
        f"| {_md_cell(_fails('DISCIPLINE'))} |",
        f"| | Coverage | Checklist areas with a verified claim. "
        f"| {_pct(sc['coverage_pct'])} ({sc['areas_covered']}/{sc['total_areas']}) "
        f"| {_md_cell(cov_note)} |",
        f"| | Utilization | Did the memo use what it found? "
        f"| {_pct(sc['utilization'])} ({sc['utilization_cited']}/{sc['utilization_total']}) "
        f"| {_md_cell(util_note)} |",
        f"| | Fact / insight recall (gold set only) | Did we surface the material facts and reach "
        f"the key judgments? | {_md_cell(_pct(sc.get('fact_insight_recall', 'n/a')))} "
        f"| {_md_cell('requires a gold set; none provided for this run' if sc.get('fact_insight_recall', 'n/a') == 'n/a' else '—')} |",
        "",
        _interpretation(sc),
        "",
    ]
    if sc["unjudged_surfaced_ids"]:
        lines += [
            f"> ⚠ {len(sc['unjudged_surfaced_ids'])} surfaced claim(s) received no verdict — "
            "the scores above cover only the judged claims (listed at the bottom).",
            "",
        ]

    # --- per-claim ledger -----------------------------------------------------
    lines += [
        "## Ledger — per-claim verdicts",
        "",
        "_Every surfaced claim, re-judged INDEPENDENTLY against its own cached source "
        "snapshot (reproducible). Failures are listed first._",
        "",
        "**Verdict meanings** — "
        "**PASS** (grounded & entailed) · "
        "🔴 **FABRICATION** (citation dead/missing or quote absent) · "
        "**MISATTRIBUTION** (quote present but statement not supported by it) · "
        "**WEAK-INFERENCE** (conclusion doesn't follow its supports) · "
        "**DISCIPLINE** (opinion-as-fact / broken fact-inference separation).",
        "",
        "| claim_id | type | verdict | cited source | offending span | reason |",
        "|---|---|---|---|---|---|",
    ]
    for v in sorted(verdicts, key=_ledger_sort_key):
        verdict = v.get("verdict", "?")
        marker = "🔴 " if verdict == "FABRICATION" else ""
        lines.append(
            f"| {_md_cell(v.get('claim_id', ''))} | {_md_cell(v.get('type', ''))} "
            f"| {marker}{_md_cell(verdict)} | {_md_cell(v.get('cited_source', ''))} "
            f"| {_md_cell(v.get('span', ''))} | {_md_cell(v.get('reason', ''))} |"
        )
    if unjudged:
        lines += ["", "## Surfaced claims with NO verdict (coverage gap in the eval)", ""]
        lines += [f"- `{cid}`" for cid in unjudged]
    lines.append("")
    out = eval_dir(run_dir) / "scorecard.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _interpretation(sc: dict) -> str:
    """One honest one-line read of the scorecard."""
    fab = sc["facts_fabrication"]
    mis = sc["facts_misattribution"]
    weak = sc["inferences_total"] - sc["inferences_pass"] - sc["inferences_discipline"]
    disc = sc["inferences_discipline"]
    if sc["facts_total"] == 0 and sc["inferences_total"] == 0:
        return "No verdicts recorded yet — run the verifier subagents, then aggregate."
    problems = []
    if fab:
        problems.append(f"{fab} fabrication(s)")
    if mis:
        problems.append(f"{mis} misattribution(s)")
    if weak:
        problems.append(f"{weak} weak inference(s)")
    if disc:
        problems.append(f"{disc} separation-discipline failure(s)")
    if not problems:
        return ("Clean pass: every surfaced fact is grounded in its own source and every "
                "inference follows from verified supports — no fabrications, misattributions, "
                "or separation failures.")
    return ("Independent verification flagged " + ", ".join(problems)
            + " among the surfaced claims — each needs fixing or dropping before sign-off "
              "(see the ledger below).")


# --- dashboard ---------------------------------------------------------------

def dashboard(runs_root: str | Path) -> Path:
    """Scan runs_root/*/*/eval/scorecard.json and write runs_root/_eval_dashboard.md."""
    runs_root = Path(runs_root)
    cards = sorted(runs_root.glob("*/*/eval/scorecard.json"))
    lines = [
        "# Eval dashboard — independent verification across runs",
        "",
        "_One row per run with an eval scorecard. All rates judged against each run's cached "
        "source snapshot._",
        "",
        "| deal | run | precision | fabrication% | misattribution% | inference-validity% "
        "| separation-discipline% | coverage% | surfaced |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for card in cards:
        sc = json.loads(card.read_text(encoding="utf-8"))
        lines.append(
            f"| {sc.get('deal', '?')} | {sc.get('run', '?')} "
            f"| {_pct(sc.get('fact_precision', 'n/a'))} "
            f"| {_pct(sc.get('fabrication_rate', 'n/a'))} "
            f"| {_pct(sc.get('misattribution_rate', 'n/a'))} "
            f"| {_pct(sc.get('inference_validity_rate', 'n/a'))} "
            f"| {_pct(sc.get('separation_discipline_rate', 'n/a'))} "
            f"| {_pct(sc.get('coverage_pct', 'n/a'))} "
            f"| {sc.get('surfaced', '?')} |"
        )
    if not cards:
        lines.append("| (no scorecards found) | | | | | | | | |")
    lines.append("")
    out = runs_root / "_eval_dashboard.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
