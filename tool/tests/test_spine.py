"""Spine smoke tests. Run directly (no pytest needed):  python tests/test_spine.py

Covers the guardrails the rest of the tool relies on:
  * schema validator REJECTS malformed claims (fact w/o quote, inference w/o supports)
  * content-addressed cache is tamper-evident
  * the quote check is whitespace-tolerant but not hallucination-tolerant
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from src.core import cache, schema, textutil  # noqa: E402


def test_schema_rejects_fact_without_quote():
    errs = schema.validate_claim(
        {"id": "x", "statement": "s", "type": "fact", "module": "research"}
    )
    assert errs, "a fact with no source/quote must be rejected"


def test_schema_rejects_inference_without_supports():
    errs = schema.validate_claim(
        {"id": "y", "statement": "s", "type": "inference", "module": "rationale"}
    )
    assert errs, "an inference with no supports must be rejected"


def test_schema_accepts_well_formed_fact():
    errs = schema.validate_claim(
        {"id": "z", "statement": "s", "type": "fact", "module": "research",
         "source_ids": ["s1"], "quote": "q"}
    )
    assert not errs, f"well-formed fact should validate, got: {errs}"


def test_cache_is_tamper_evident(tmp_dir: Path):
    h, rel = cache.store(tmp_dir, b"hello world")
    assert cache.verify_integrity(tmp_dir, h)
    # corrupt the cached bytes
    (tmp_dir / rel).write_bytes(b"tampered")
    assert not cache.verify_integrity(tmp_dir, h), "tampered cache must fail integrity"


def test_quote_check_is_whitespace_tolerant_not_hallucination_tolerant():
    src = "The offer is   $100.00\n per share."
    assert textutil.quote_present("The offer is $100.00 per share.", src)
    assert not textutil.quote_present("The offer is $140.00 per share.", src)


def main() -> int:
    import tempfile

    passed = 0
    failed = 0
    tests = [
        test_schema_rejects_fact_without_quote,
        test_schema_rejects_inference_without_supports,
        test_schema_accepts_well_formed_fact,
        test_quote_check_is_whitespace_tolerant_not_hallucination_tolerant,
    ]
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {t.__name__}: {e}")
            failed += 1

    # cache test needs a temp dir
    with tempfile.TemporaryDirectory() as d:
        try:
            test_cache_is_tamper_evident(Path(d))
            print("  ✅ test_cache_is_tamper_evident")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ test_cache_is_tamper_evident: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    raise SystemExit(main())
