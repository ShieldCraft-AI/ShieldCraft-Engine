"""Deterministic governance map linking policy rules and readiness gates
to source documents and enforcement types.

This module is data-only and computes file hashes at import time so tests
can detect when governance documents change without corresponding code updates.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Optional


def _file_hash(path: str) -> Optional[str]:
    p = Path(path)
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


# Governance map keyed by policy/gate codes
GOVERNANCE_MAP: Dict[str, Dict] = {
    # Semantic strictness rules
    "invariants_empty": {
        "file": "docs/INVARIANTS.md",
        "section": "Required invariants",
        "enforcement": "hard",
        "description": "Invariants must be declared to reason about instruction safety",
    },
    "model_empty": {
        "file": "docs/CONTRACTS.md",
        "section": "Model contract",
        "enforcement": "hard",
        "description": "Model must provide dependency graph context",
    },
    "sections_empty": {
        "file": "docs/CONTRACTS.md",
        "section": "Sections and layout",
        "enforcement": "soft",
        "description": "Sections are recommended for author ergonomics",
    },

    # Readiness gates
    "tests_attached": {
        "file": "docs/OPERATIONAL_READINESS.md",
        "section": "Tests Attached",
        "enforcement": "hard",
        "description": "Tests must be attached for operational readiness",
    },
    "spec_fuzz_stability": {
        "file": "docs/OPERATIONAL_READINESS.md",
        "section": "Spec Fuzz Stability",
        "enforcement": "advisory",
        "description": "Spec should be stable under small perturbations",
    },
    "persona_no_veto": {
        "file": "docs/CONTRACTS.md",
        "section": "Persona Veto",
        "enforcement": "soft",
        "description": "Persona vetoes are advisory and should be inspected",
    },
}


def get_governance_for(code: str) -> Dict:
    entry = dict(GOVERNANCE_MAP.get(code, {}))
    if entry.get("file"):
        entry["file_hash"] = _file_hash(entry["file"])
    return entry


def all_mappings() -> Dict[str, Dict]:
    out = {}
    for k, v in GOVERNANCE_MAP.items():
        out[k] = get_governance_for(k)
    return out
