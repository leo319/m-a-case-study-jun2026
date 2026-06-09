"""Run-space management: run directories, the stage manifest, and the audit log.

A "run" is one execution of the pipeline for one deal, living under
runs/<deal>/<ts>/. The orchestrator skill calls these helpers (via Bash) to
create a run, track which stage is where, and — per the Model C audit
requirement — record every gate's presented artifact plus the analyst's steering.

The audit log is written two ways:
  * steering_log.md   — human/auditor-readable narrative of the run
  * conversation.jsonl — machine-readable, one record per gate, for replay
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ..core.paths import CACHE_ROOT, RUNS_ROOT, RunContext

_PACIFIC = ZoneInfo("America/Los_Angeles")

# The full pipeline, single source of truth. Stages marked active=False are
# planned but not yet implemented (Milestone 3+). The orchestrator renders this
# map to the analyst at the start of every run so they know the whole journey.
PIPELINE_STAGES = [
    {"key": "intake", "title": "Intake & Scoping", "gate": "Confirm deal scope + steering", "active": True},
    {"key": "source_plan", "title": "Source Planning", "gate": "Approve / add / remove sources", "active": True},
    {"key": "research", "title": "Research, Grounding & Verification", "gate": "Review brief + quarantines, steer", "active": True},
    {"key": "expert", "title": "Expert Analysis", "gate": "Review preliminary analysis, steer", "active": True},
    {"key": "redteam", "title": "Red-Team & Finalize", "gate": "Final sign-off", "active": True},
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ts_slug() -> str:
    # Readable, Pacific time. No ':' — Windows forbids it in paths — so HHMM not HH:MM.
    return datetime.now(_PACIFIC).strftime("%Y-%m-%d %H%M")


@dataclass(frozen=True)
class Run:
    ctx: RunContext
    deal_id: str

    @property
    def run_dir(self) -> Path:
        return self.ctx.run_dir

    @property
    def manifest_path(self) -> Path:
        return self.ctx.audit("manifest.json")

    @property
    def steering_log_path(self) -> Path:
        return self.ctx.audit("steering_log.md")

    @property
    def conversation_path(self) -> Path:
        return self.ctx.audit("conversation.jsonl")


def create_run(deal_id: str, *, cache_dir: Path | None = None, ts: str | None = None) -> Run:
    ts = ts or _ts_slug()
    run_dir = RUNS_ROOT / deal_id / ts
    cache = cache_dir if cache_dir is not None else CACHE_ROOT
    ctx = RunContext(run_dir=run_dir, cache_dir=cache).ensure()
    run = Run(ctx=ctx, deal_id=deal_id)
    manifest = {
        "deal_id": deal_id,
        "created_at": _now_iso(),
        "stages": [
            {"key": s["key"], "title": s["title"], "active": s["active"],
             "status": "pending" if s["active"] else "not_implemented"}
            for s in PIPELINE_STAGES
        ],
    }
    save_manifest(run, manifest)
    # seed the human-readable log
    run.steering_log_path.write_text(
        f"# Steering log — {deal_id}\n\n"
        f"Run created: {manifest['created_at']}\n\n"
        f"This log records every gate: what the tool presented and how the analyst steered.\n\n",
        encoding="utf-8",
    )
    run.conversation_path.write_text("", encoding="utf-8")
    return run


def open_run(run_dir: str | Path, *, cache_dir: Path | None = None) -> Run:
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "audit" / "manifest.json").read_text(encoding="utf-8"))
    cache = cache_dir if cache_dir is not None else CACHE_ROOT
    ctx = RunContext(run_dir=run_dir, cache_dir=cache)
    return Run(ctx=ctx, deal_id=manifest["deal_id"])


def load_manifest(run: Run) -> dict:
    return json.loads(run.manifest_path.read_text(encoding="utf-8"))


def save_manifest(run: Run, manifest: dict) -> None:
    run.manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def set_stage_status(run: Run, stage_key: str, status: str) -> None:
    manifest = load_manifest(run)
    for s in manifest["stages"]:
        if s["key"] == stage_key:
            s["status"] = status
    save_manifest(run, manifest)


def record_gate(run: Run, *, stage: str, presented: str, steering: str,
                artifacts: list[str] | None = None) -> None:
    """Append one gate interaction to both audit logs."""
    ts = _now_iso()
    artifacts = artifacts or []
    record = {
        "ts": ts,
        "stage": stage,
        "presented": presented,
        "steering": steering,
        "artifacts": artifacts,
    }
    with open(run.conversation_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    md = [f"## Gate — {stage}  ({ts})", ""]
    if artifacts:
        md.append("Artifacts: " + ", ".join(f"`{a}`" for a in artifacts))
        md.append("")
    md.append("**Tool presented:**")
    md.append("")
    md.append(presented.strip())
    md.append("")
    md.append("**Analyst steering:**")
    md.append("")
    md.append(steering.strip() or "_(approved, no changes)_")
    md.append("")
    with open(run.steering_log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")


def pipeline_map_markdown() -> str:
    """The full-pipeline overview the orchestrator shows the analyst up front."""
    lines = ["**Merger Analysis pipeline — the full journey**", ""]
    for i, s in enumerate(PIPELINE_STAGES, 1):
        tag = "" if s["active"] else "  _(coming in a later milestone)_"
        lines.append(f"{i}. **{s['title']}**{tag}")
        lines.append(f"   - 🚦 Gate: {s['gate']}")
    lines.append("")
    lines.append("At each 🚦 gate I stop, show you what I have, and wait for your steering before continuing.")
    return "\n".join(lines)
