"""Path resolution for the spine.

Layout (per PLAN.md §7):
  /cache/                 content-addressed source cache (shared, gitignored)
  /runs/<deal>/<ts>/      per-run outputs: claims.jsonl, source_registry.json, reports
  /src/schemas/           claim + source JSON schemas

A RunContext bundles the handful of paths every hook needs so callers pass one
object instead of four strings.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# tool/  (two parents up from this file: src/core/paths.py -> src -> tool)
TOOL_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_DIR = TOOL_ROOT / "src" / "schemas"
CACHE_ROOT = TOOL_ROOT / "cache"
RUNS_ROOT = TOOL_ROOT / "runs"


@dataclass(frozen=True)
class RunContext:
    """Everything a stage/hook needs to read and write one run."""
    run_dir: Path
    cache_dir: Path

    @property
    def claims_path(self) -> Path:
        return self.run_dir / "claims.jsonl"

    @property
    def registry_path(self) -> Path:
        return self.run_dir / "source_registry.json"

    @property
    def verification_report_path(self) -> Path:
        return self.run_dir / "verification_report.md"

    def ensure(self) -> "RunContext":
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self


def run_context(run_dir: str | Path, cache_dir: str | Path | None = None) -> RunContext:
    """Build a RunContext. Cache defaults to the shared /cache root, but a run may
    use an isolated cache (the milestone-1 demo does this for determinism)."""
    run_dir = Path(run_dir)
    cache_dir = Path(cache_dir) if cache_dir is not None else CACHE_ROOT
    return RunContext(run_dir=run_dir, cache_dir=cache_dir)
