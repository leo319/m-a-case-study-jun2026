"""JSON-schema loading + validation for claims and sources.

This is the first deterministic guardrail: a malformed claim (e.g. a fact with no
quote, or an inference with no supports) is rejected before it can be verified or
rendered. Conditional rules live in the schema files (allOf/if-then).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator

from .paths import SCHEMA_DIR


@lru_cache(maxsize=None)
def _validator(name: str) -> Draft202012Validator:
    schema_path = SCHEMA_DIR / f"{name}.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _errors(name: str, obj: dict) -> list[str]:
    v = _validator(name)
    out = []
    for err in sorted(v.iter_errors(obj), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out


def validate_claim(claim: dict) -> list[str]:
    return _errors("claim", claim)


def validate_source(source: dict) -> list[str]:
    return _errors("source", source)


def validate_all(claims: list[dict], sources: dict[str, dict]) -> dict[str, list[str]]:
    """Return {object_id: [errors]} for every invalid object. Empty dict == all valid."""
    problems: dict[str, list[str]] = {}
    for s_id, s in sources.items():
        errs = validate_source(s)
        if errs:
            problems[f"source:{s_id}"] = errs
    for c in claims:
        c_id = c.get("id", "<no-id>")
        errs = validate_claim(c)
        if errs:
            problems[f"claim:{c_id}"] = errs
    return problems
