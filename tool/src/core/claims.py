"""Read/write claims.jsonl — the audit spine, one claim per line."""
from __future__ import annotations

import json
from pathlib import Path


def load_claims(path: Path) -> list[dict]:
    claims: list[dict] = []
    if not Path(path).exists():
        return claims
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                claims.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{lineno}: invalid JSON: {e}") from e
    return claims


def save_claims(path: Path, claims: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for claim in claims:
            f.write(json.dumps(claim, ensure_ascii=False))
            f.write("\n")


def index_by_id(claims: list[dict]) -> dict[str, dict]:
    return {c["id"]: c for c in claims}
