"""Semantic strictness policy controller.

Centralizes strictness rule definitions and maps environment flags to active
rule-sets. Rules are data-driven and deterministic to support auditable
policy decisions.
"""
from __future__ import annotations

import os
from typing import Dict, Iterable, List


RULES = {
    1: [
        {
            "section": "sections",
            "code": "sections_empty",
            "message": "spec must declare a non-empty 'sections' array",
            "location": "/sections",
            "type": "list",
            "expected": "non-empty array",
            "rationale": "Sections is required by schema and empty in normalized skeleton",
        }
    ],
    2: [
        {
            "section": "invariants",
            "code": "invariants_empty",
            "message": "spec must declare a non-empty 'invariants' list",
            "location": "/invariants",
            "type": "list",
            "expected": "non-empty array",
            "rationale": "Invariants are required for instruction validation and are missing in skeleton",
        },
        {
            "section": "model",
            "code": "model_empty",
            "message": "spec must declare a non-empty 'model' object",
            "location": "/model",
            "type": "dict",
            "expected": "non-empty object",
            "rationale": "Model provides dependency graph context and is empty in skeleton",
        },
    ],
}


class SemanticStrictnessPolicy:
    """Controller for semantic strictness policy.

    Usage: call `SemanticStrictnessPolicy.from_env()` to load enabled levels,
    then inspect `active_levels()` and `enforced_rules()`.
    """

    def __init__(self, active_levels: Iterable[int]):
        self._active = sorted(set(int(x) for x in active_levels))

    @classmethod
    def from_env(cls) -> "SemanticStrictnessPolicy":
        # Default policy: enable Level 1 by default unless explicitly disabled.
        # Use `SEMANTIC_STRICTNESS_DISABLED=1` to opt-out of default strictness.
        if os.getenv("SEMANTIC_STRICTNESS_DISABLED", "0") == "1":
            active = []
        else:
            # Start with Level 1 by default; additional levels may be opt-in via
            # `SEMANTIC_STRICTNESS_LEVEL_N=1` environment variables.
            active = [1]
        for lvl in sorted(RULES.keys()):
            if os.getenv(f"SEMANTIC_STRICTNESS_LEVEL_{lvl}", "0") == "1":
                if lvl not in active:
                    active.append(lvl)
        return cls(active)

    def active_levels(self) -> List[int]:
        return list(self._active)

    def enforced_rules(self) -> List[Dict]:
        out: List[Dict] = []
        for lvl in self._active:
            out.extend(RULES.get(lvl, []))
        return out

    def to_dict(self) -> Dict:
        return {
            "active_levels": self.active_levels(),
            "enforced_sections": [
                {"section": r["section"], "rationale": r["rationale"], "code": r["code"]} for r in self.enforced_rules()
            ],
        }
