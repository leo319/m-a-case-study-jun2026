"""Content-addressed source cache.

Fetched content is stored under cache/<aa>/<sha256>, keyed by the sha256 of its
bytes. Two consequences the plan leans on:
  * reproducibility — a claim's quote is checked against the exact bytes that were
    fetched, even after the live web changes.
  * tamper-evidence — verify_integrity() recomputes the hash, so a corrupted or
    swapped cache file is caught before a quote check can pass against it.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path_for(cache_dir: Path, content_hash: str) -> Path:
    # shard by first two hex chars to keep directories small
    return cache_dir / content_hash[:2] / content_hash


def relpath_for(content_hash: str) -> str:
    """The local_path stored in the registry, relative to the cache root."""
    return f"{content_hash[:2]}/{content_hash}"


def store(cache_dir: Path, data: bytes) -> tuple[str, str]:
    """Store bytes; return (content_hash, local_path_relative_to_cache_dir)."""
    content_hash = sha256_bytes(data)
    dest = _path_for(cache_dir, content_hash)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(data)
    return content_hash, relpath_for(content_hash)


def load(cache_dir: Path, content_hash: str) -> bytes:
    return _path_for(cache_dir, content_hash).read_bytes()


def exists(cache_dir: Path, content_hash: str) -> bool:
    return _path_for(cache_dir, content_hash).exists()


def verify_integrity(cache_dir: Path, content_hash: str) -> bool:
    """True iff the cached file exists and its bytes still hash to content_hash."""
    if not exists(cache_dir, content_hash):
        return False
    return sha256_bytes(load(cache_dir, content_hash)) == content_hash
