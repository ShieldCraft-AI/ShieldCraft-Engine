from typing import Any, Dict
from shieldcraft.util.json_canonicalizer import canonicalize
from shieldcraft.observability import emit_persona_event


def record_decision(engine, persona_id: str, phase: str, decision: Dict[str, Any], severity: str = "info") -> None:
    """Record a persona decision as a PersonaEvent with capability 'decision'.

    Decision payload is canonicalized and emitted via observability for audit.
    Also stores a runtime list on the engine object for quick lookup in guards.
    """
    payload_ref = canonicalize(decision)
    # Use capability 'decision' for recorded persona decisions
    emit_persona_event(engine, persona_id, "decision", phase, payload_ref, severity)
    if not hasattr(engine, "_persona_decisions"):
        engine._persona_decisions = []  # type: ignore
    engine._persona_decisions.append({"persona_id": persona_id, "phase": phase, "decision": decision})
