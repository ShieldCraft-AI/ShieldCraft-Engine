from typing import List
from shieldcraft.observability import read_persona_events


def enforce_manifest_emission_ok() -> None:
    """Enforce persona guard before emitting artifacts.

    Rules:
    - Every persona event (annotate|veto) must be accompanied by a 'decision' event
      for the same persona + phase, otherwise halt emission.
    - Veto events are terminal and must be visible to preflight (engine handles vetoes already).
    """
    import os

    # Only enforce when persona subsystem is enabled to avoid cross-test contamination
    if os.getenv("SHIELDCRAFT_PERSONA_ENABLED", "0") != "1":
        return

    events = read_persona_events()
    if not events:
        return

    # Build index of decisions by persona+phase
    decisions = set()
    for e in events:
        if e.get("capability") == "decision":
            decisions.add((e.get("persona_id"), e.get("phase")))

    violations: List[str] = []
    for e in events:
        cap = e.get("capability")
        if cap in ("annotate", "veto"):
            key = (e.get("persona_id"), e.get("phase"))
            if key not in decisions:
                violations.append(
                    f"persona_unlogged_action:{e.get('persona_id')}:{e.get('capability')}@{e.get('phase')}")

    if violations:
        # Halt emission by raising a deterministic RuntimeError
        raise RuntimeError(";".join(sorted(violations)))
