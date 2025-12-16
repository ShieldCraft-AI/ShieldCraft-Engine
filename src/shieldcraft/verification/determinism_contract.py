"""Determinism contract definitions and validators.

Defines the scope of determinism guarantees and simple validators used by
the replay and verification systems.
"""
from typing import Dict, Any


REQUIRED_KEYS = ["spec", "checklist", "seeds"]


def validate_record(record: Dict[str, Any]) -> None:
    for k in REQUIRED_KEYS:
        if k not in record:
            raise RuntimeError(f"determinism_record_missing:{k}")


def ensure_seed_present(record: Dict[str, Any], name: str) -> None:
    seeds = record.get("seeds", {})
    if name not in seeds:
        raise RuntimeError(f"missing_seed:{name}")
