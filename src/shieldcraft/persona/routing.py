"""Persona routing table: maps {phase} -> allowed persona names.

This module centralizes static, deterministic routing of personas to phases.
By default, routing is empty and discovery falls back to persona `scope` rules.
Routing is pure configuration and deterministic (lexicographic ordering applied where relevant).
"""
from typing import Dict, List, Optional

# Example shape: {"checklist": ["security_auditor", "licensor"], "preflight": ["governance"]}
DEFAULT_ROUTING: Dict[str, List[str]] = {}


def get_allowed_persona_names_for_phase(phase: str) -> Optional[List[str]]:
    """Return list of allowed persona names for `phase` or None if not configured."""
    if not DEFAULT_ROUTING:
        return None
    return sorted(DEFAULT_ROUTING.get(phase, []))


def set_routing(mapping: Dict[str, List[str]]) -> None:
    """Set routing mapping for runtime/testing. Mapping should be deterministic (string lists).

    WARNING: This mutates module-level routing state and is intended to be used in deterministic
    test and configuration flows only. Production usage should set `DEFAULT_ROUTING` via
    a well-reviewed configuration change.
    """
    global DEFAULT_ROUTING
    DEFAULT_ROUTING = {k: sorted(v) for k, v in mapping.items()}
