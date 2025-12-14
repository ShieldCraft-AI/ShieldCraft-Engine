"""Definitions for readiness: what gates must pass for SE readiness."""
from typing import List


REQUIRED_GATES: List[str] = [
    "spec_fuzz_stability",
    "tests_attached",
    "persona_no_veto",
    "determinism_replay",
]


def validate_gates_list(gates: List[str]) -> None:
    for g in gates:
        if g not in REQUIRED_GATES:
            raise RuntimeError(f"unknown_readiness_gate:{g}")
