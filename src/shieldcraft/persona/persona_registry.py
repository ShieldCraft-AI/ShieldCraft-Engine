"""Registry for programmatic persona registrations for tests and runtimes.

This allows personas to be registered in-memory for deterministic evaluation
without relying on filesystem persona files.
"""
from typing import List, Dict, Any
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
    res = []
    for p in list_personas():
        if not p.scope or 'all' in p.scope or phase in p.scope:
            res.append(p)
    return res
