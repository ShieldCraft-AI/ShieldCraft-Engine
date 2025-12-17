"""Validator that records persona vetoes as advisory diagnostics (non-authoritative).

Historically persona vetoes raised a RuntimeError and caused refusal; under Phase 15 we treat
personas as advisory specialists only: vetoes are recorded for auditability but DO NOT alter
engine control flow or produce REFUSAL/BLOCKER outcomes.
"""
from typing import Any, Dict
from shieldcraft.util.json_canonicalizer import canonicalize


def enforce_persona_veto(engine) -> None:
    if not hasattr(engine, "_persona_vetoes") or not engine._persona_vetoes:
        return None

    # Deterministic selection: sort by severity then persona_id
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}

    def _key(v: Dict[str, Any]):
        return (severity_order.get(v.get("severity"), 0), v.get("persona_id"))

    sel = sorted(engine._persona_vetoes, key=_key, reverse=True)[0]
    # include canonicalized explanation for machine readability
    expl = canonicalize(sel.get("explanation", {}))
    # Record as a DIAGNOSTIC on the engine context instead of raising
    try:
        if getattr(engine, "checklist_context", None):
            engine.checklist_context.record_event("G7_PERSONA_VETO", "preflight", "DIAGNOSTIC", message="persona veto advisory (non-authoritative)", evidence={"persona_id": sel.get('persona_id'), "code": sel.get('code'), "explanation": expl})
    except Exception:
        pass
    # Keep a pointer to the selected veto for observability, but do not raise
    try:
        engine._persona_veto_selected = sel
    except Exception:
        pass
    return sel
