"""Persona contract definitions and validators."""
from typing import List


ALLOWED_ACTIONS: List[str] = ["annotate", "veto", "suggest", "rank"]


def validate_action(action: str) -> bool:
    """Return True if action is permitted by contract."""
    return action in ALLOWED_ACTIONS


def ensure_allowed(persona, action: str) -> None:
    if not validate_action(action):
        raise ValueError(f"persona_action_not_allowed:{action}")
    if action not in (persona.allowed_actions or []):
        raise ValueError(f"persona_action_not_permitted_by_persona:{action}")
