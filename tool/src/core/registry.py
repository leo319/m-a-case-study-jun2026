"""Read/write source_registry.json — the {id -> source} map.

Stored on disk as a JSON object keyed by source id for O(1) lookup by the verifier.
"""
from __future__ import annotations

import json
from pathlib import Path


def load_registry(path: Path) -> dict[str, dict]:
    if not Path(path).exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # tolerate either {id: source} or [source, ...]
    if isinstance(data, list):
        return {s["id"]: s for s in data}
    return data


def save_registry(path: Path, registry: dict[str, dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        f.write("\n")


def add_source(registry: dict[str, dict], source: dict) -> dict[str, dict]:
    registry[source["id"]] = source
    return registry
