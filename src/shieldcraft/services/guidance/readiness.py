"""Deterministic readiness gate classifications and grading.

Provides mapping of readiness gates to blocking/non-blocking classification
and a simple deterministic grade derived from failure counts.
"""
from __future__ import annotations

from typing import Dict


# Gate classification map: True => blocking, False => non-blocking
GATE_BLOCKING: Dict[str, bool] = {
    "spec_fuzz_stability": False,
    "tests_attached": True,
    "persona_no_veto": False,
    "determinism_replay": True,
}


def is_blocking(gate: str) -> bool:
    return GATE_BLOCKING.get(gate, False)


def grade_from_counts(blocking: int, non_blocking: int) -> str:
    # Deterministic grading rules (informational only)
    if blocking > 0:
        return "F"
    if non_blocking >= 3:
        return "C"
    if non_blocking == 2:
        return "B"
    if non_blocking == 1:
        return "A"
    return "A"
