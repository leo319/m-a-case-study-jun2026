"""Milestone 1 proof — fabrication is structurally caught, before any agent exists.

Self-contained and deterministic: no network, no model. It

  1. seeds an isolated content-addressed cache from a local fixture,
  2. registers exactly one real source (the fixture) — and deliberately NOT the
     fabricated one,
  3. writes five claims spanning every outcome the spine must handle,
  4. runs the schema validator, then the deterministic citation verifier,
  5. asserts each claim landed in the expected state and prints a ✅/❌ table.

Run:
  python scripts/run_milestone1_demo.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Make `src` importable when run as a plain script.
TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

# Windows consoles default to cp1252; force UTF-8 so the ✅/❌ status markers render.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from src.core import cache, textutil  # noqa: E402
from src.core import claims as claims_io  # noqa: E402
from src.core import registry as registry_io  # noqa: E402
from src.core import schema  # noqa: E402
from src.core.paths import run_context  # noqa: E402
from src.hooks import verify_citations  # noqa: E402

FIXTURE = TOOL_ROOT / "tests" / "fixtures" / "synthetic_press_release.txt"

# The quote below is copied verbatim from the fixture, so it must be found.
REAL_QUOTE = "$100.00 per share in cash, representing a premium of\n35% over Beta's unaffected closing price."
# This text never appears in the fixture — a plausible-sounding but ungrounded number.
ABSENT_QUOTE = "$140.00 per share, a premium of 70% over the unaffected price"


def build_demo_run():
    run_dir = TOOL_ROOT / "runs" / "_demo_milestone1"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    # Isolated cache so the proof is fully reproducible and never touches /cache.
    ctx = run_context(run_dir, cache_dir=run_dir / "cache").ensure()

    # 1. Seed the cache with the fixture and register it as the only real source.
    data = FIXTURE.read_bytes()
    content_hash, local_path = cache.store(ctx.cache_dir, data)
    registry = {
        "s_press": {
            "id": "s_press",
            "title": "Synthetic press release (FIXTURE)",
            "url": "https://example.com/fixture/press-release",
            "tier": "T2",
            "retrieved_at": "2026-06-06T00:00:00+00:00",
            "content_hash": content_hash,
            "local_path": local_path,
            "media_type": "text/plain",
        }
        # NOTE: 's_ghost' is intentionally absent — it models a fabricated citation.
    }
    registry_io.save_registry(ctx.registry_path, registry)

    # 2. Five claims covering every outcome.
    claims = [
        {  # grounded fact — quote really is in the source
            "id": "c0001", "type": "fact", "module": "research",
            "statement": "The offer is $100.00/share in cash, a 35% premium.",
            "source_ids": ["s_press"], "quote": REAL_QUOTE, "confidence": 0.9,
        },
        {  # fabricated number — quote absent from the source
            "id": "c0002", "type": "fact", "module": "tailrisk",
            "statement": "The offer is $140.00/share, a 70% premium.",
            "source_ids": ["s_press"], "quote": ABSENT_QUOTE, "confidence": 0.5,
        },
        {  # fabricated/dead citation — source not in the registry
            "id": "c0003", "type": "fact", "module": "research",
            "statement": "A regulator has already cleared the deal.",
            "source_ids": ["s_ghost"], "quote": "the transaction has received unconditional clearance",
            "confidence": 0.4,
        },
        {  # inference built on a verified claim -> should verify
            "id": "c0004", "type": "inference", "module": "rationale",
            "statement": "A 35% cash premium signals confidence in the target's standalone value.",
            "supports": ["c0001"], "confidence": 0.6,
        },
        {  # inference built on a quarantined claim -> should quarantine
            "id": "c0005", "type": "inference", "module": "rationale",
            "statement": "The 70% premium implies an aggressive, possibly overpriced bid.",
            "supports": ["c0002"], "confidence": 0.6,
        },
    ]
    claims_io.save_claims(ctx.claims_path, claims)
    return ctx


def main() -> int:
    print("=" * 70)
    print("MILESTONE 1 PROOF — deterministic citation verifier")
    print("=" * 70)

    ctx = build_demo_run()

    # Sanity: the verbatim quote really is present in the fixture (guards the test).
    assert textutil.quote_present(REAL_QUOTE, FIXTURE.read_text(encoding="utf-8")), \
        "fixture/quote drift: REAL_QUOTE is not actually in the fixture"

    # Step 1 — schema validation must pass.
    claims = claims_io.load_claims(ctx.claims_path)
    sources = registry_io.load_registry(ctx.registry_path)
    problems = schema.validate_all(claims, sources)
    print(f"\n[1] schema validation: {'OK' if not problems else 'FAILED'}")
    if problems:
        for k, errs in problems.items():
            print(f"    {k}: {errs}")
        return 1

    # Step 2 — run the deterministic verifier.
    report = verify_citations.verify(ctx)

    expected = {
        "c0001": "verified",
        "c0002": "quarantined",
        "c0003": "quarantined",
        "c0004": "verified",
        "c0005": "quarantined",
    }
    why = {
        "c0001": "grounded fact — quote present in source",
        "c0002": "fabricated number — quote absent from source",
        "c0003": "fabricated/dead citation — source not in registry",
        "c0004": "inference built on a verified claim",
        "c0005": "inference built on a quarantined claim",
    }

    verified_claims = claims_io.load_claims(ctx.claims_path)
    by_id = claims_io.index_by_id(verified_claims)

    print("\n[2] verifier results:\n")
    print(f"    {'claim':6} {'expected':12} {'actual':12} {'':3} reason")
    print(f"    {'-'*6} {'-'*12} {'-'*12} {'-'*3} {'-'*40}")
    all_ok = True
    for cid, exp in expected.items():
        actual = by_id[cid]["status"]
        ok = actual == exp
        all_ok = all_ok and ok
        print(f"    {cid:6} {exp:12} {actual:12} {'✅' if ok else '❌'} {why[cid]}")

    print("\n[3] verification report written to:")
    print(f"    {ctx.verification_report_path.relative_to(TOOL_ROOT)}")
    print(f"\n    fabricated/dead caught: {report['fabricated_or_dead']}   "
          f"quote-absent caught: {report['quote_absent']}")

    print("\n" + "=" * 70)
    if all_ok:
        print("RESULT: ✅ PASS — every fabricated/ungrounded claim was quarantined.")
        print("        No agent involved. The guardrail holds by construction.")
    else:
        print("RESULT: ❌ FAIL — see mismatches above.")
    print("=" * 70)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
