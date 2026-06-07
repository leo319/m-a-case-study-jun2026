"""Path resolution for the spine.

Layout (per PLAN.md §7, refined):
  /config/                deal-agnostic input knobs (coverage checklist, ...)   ✏️ editable
  /deal_spec/             one yaml per deal (deal-specific inputs)              ✏️ editable
  /cache/                 content-addressed source cache (shared, gitignored)  🤖 generated
  /runs/<deal>/<ts>/      one run, split into:                                  🤖 generated
      artifacts/            files the analyst reviews (briefs, memo, findings, source plan)
      audit/                full audit trail (claims, registry, reports, logs, specs, intake)
  /src/schemas/           claim + source JSON schemas

A RunContext bundles the paths every hook needs. Outputs are split so it's obvious
what's for human review (artifacts/) vs. the machine-readable audit trail (audit/).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# tool/  (two parents up from this file: src/core/paths.py -> src -> tool)
TOOL_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_DIR = TOOL_ROOT / "src" / "schemas"
CONFIG_DIR = TOOL_ROOT / "config"
CACHE_ROOT = TOOL_ROOT / "cache"
RUNS_ROOT = TOOL_ROOT / "runs"

ARTIFACTS = "artifacts"
AUDIT = "audit"

# Files that go in artifacts/ (everything else a run writes goes in audit/).
ARTIFACT_FILES = {
    "research_brief.md",
    "preliminary_memo.md",
    "research_findings.md",
    "source_plan.md",
}


def artifacts_dir(run_dir: str | Path) -> Path:
    return Path(run_dir) / ARTIFACTS


def audit_dir(run_dir: str | Path) -> Path:
    return Path(run_dir) / AUDIT


def out_path(run_dir: str | Path, name: str) -> Path:
    """Resolve a run output file to artifacts/ or audit/ by its name."""
    sub = ARTIFACTS if name in ARTIFACT_FILES else AUDIT
    return Path(run_dir) / sub / name


def claims_path(run_dir: str | Path) -> Path:
    return audit_dir(run_dir) / "claims.jsonl"


def registry_path(run_dir: str | Path) -> Path:
    return audit_dir(run_dir) / "source_registry.json"


@dataclass(frozen=True)
class RunContext:
    """Everything a stage/hook needs to read and write one run."""
    run_dir: Path
    cache_dir: Path

    @property
    def artifacts_dir(self) -> Path:
        return self.run_dir / ARTIFACTS

    @property
    def audit_dir(self) -> Path:
        return self.run_dir / AUDIT

    def artifact(self, name: str) -> Path:
        return self.artifacts_dir / name

    def audit(self, name: str) -> Path:
        return self.audit_dir / name

    @property
    def claims_path(self) -> Path:
        return self.audit_dir / "claims.jsonl"

    @property
    def registry_path(self) -> Path:
        return self.audit_dir / "source_registry.json"

    @property
    def verification_report_path(self) -> Path:
        return self.audit_dir / "verification_report.md"

    def ensure(self) -> "RunContext":
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self


def run_context(run_dir: str | Path, cache_dir: str | Path | None = None) -> RunContext:
    """Build a RunContext. Cache defaults to the shared /cache root, but a run may
    use an isolated cache (the milestone-1 demo does this for determinism)."""
    run_dir = Path(run_dir)
    cache_dir = Path(cache_dir) if cache_dir is not None else CACHE_ROOT
    return RunContext(run_dir=run_dir, cache_dir=cache_dir)
