"""Registry for programmatic persona registrations for tests and runtimes.

This allows personas to be registered in-memory for deterministic evaluation
without relying on filesystem persona files.
"""
from typing import List
from shieldcraft.persona import Persona

_REGISTRY: List[Persona] = []


def register_persona(persona: Persona) -> None:
    # Deduplicate by name deterministically
    global _REGISTRY
    # Replace any existing persona with same name
    _REGISTRY = [p for p in _REGISTRY if p.name != persona.name]
    _REGISTRY.append(persona)


def clear_registry() -> None:
    global _REGISTRY
    _REGISTRY = []


def list_personas() -> List[Persona]:
    # Return sorted copy for deterministic iteration
    return sorted(list(_REGISTRY), key=lambda p: p.name)


def find_personas_for_phase(phase: str) -> List[Persona]:
    """Return personas applicable to a phase.

    Behavior:
    - If a static routing table is configured (see `persona.routing`), filter
      by allowed persona names for the phase. Otherwise fall back to persona
      `scope` rules (existing behavior).
    - Deterministic ordering (sorted by persona.name) is preserved.
    """
    from shieldcraft.persona.routing import get_allowed_persona_names_for_phase

    res = []
    for p in list_personas():
        if not p.scope or 'all' in p.scope or phase in p.scope:
            res.append(p)

    allowed = get_allowed_persona_names_for_phase(phase)
    if allowed is None:
        return res

    # Filter by allowed names deterministically
    allowed_set = set(allowed)
    return [p for p in res if p.name in allowed_set]
