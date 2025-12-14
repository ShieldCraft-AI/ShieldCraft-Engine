"""Validator that enforces persona vetoes block progression."""
from typing import Any, Dict
from shieldcraft.util.json_canonicalizer import canonicalize


def enforce_persona_veto(engine) -> None:
    if not hasattr(engine, "_persona_vetoes") or not engine._persona_vetoes:
        return

    # Deterministic selection: sort by severity then persona_id
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}

    def _key(v: Dict[str, Any]):
        return (severity_order.get(v.get("severity"), 0), v.get("persona_id"))

    sel = sorted(engine._persona_vetoes, key=_key, reverse=True)[0]
    # include canonicalized explanation for machine readability
    expl = canonicalize(sel.get("explanation", {}))
    raise RuntimeError(f"persona_veto:{sel.get('persona_id')}:{sel.get('code')}:{expl}")
