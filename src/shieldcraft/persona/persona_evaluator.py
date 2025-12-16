"""Evaluate persona constraints and veto rules against checklist items.

This evaluator is intentionally conservative: personas may only emit vetoes
or constraints (simple key sets). They cannot create new items or mutate
identifiers (`id`, `ptr`). All decisions are recorded via the persona APIs
for auditability.
"""
from typing import Any, Dict, List
from shieldcraft.persona import PersonaContext
from shieldcraft.persona import emit_veto
from shieldcraft.persona.decision_record import record_decision


def _matches(item: Dict[str, Any], match: Dict[str, Any]) -> bool:
    # Simple matching helper: all key/value pairs must equal the item's values
    for k, v in (match or {}).items():
        if item.get(k) != v:
            return False
    return True


def evaluate_personas(engine, personas: List[Any], items: List[Dict[str, Any]], phase: str = "checklist") -> Dict[str, Any]:
    """Evaluate personas and apply constraints deterministically.

    Returns a dict with summary: {"vetoes": [...], "constraints_applied": N}
   """
    vetoes = []
    applied = 0
    # Do not mutate `items` in-place. Collect constraints to be applied by the caller.
    constraints_to_apply = []

    # Iterate deterministically by persona name
    for p in sorted(personas, key=lambda x: x.name):
        ctx = PersonaContext(
            name=p.name,
            role=p.role,
            display_name=p.display_name,
            scope=p.scope,
            allowed_actions=p.allowed_actions,
            constraints=p.constraints,
        )

        # Evaluate veto rules (if any)
        for rule in p.constraints.get("veto", []):
            match = rule.get("match", {})
            code = rule.get("code", "veto")
            explanation = rule.get("explanation", {"explanation_code": "unspecified", "details": ""})
            for item in items:
                if _matches(item, match):
                    # Record veto via persona API (ensures auditability and deterministic recording)
                    emit_veto(engine, ctx, phase, code, explanation, severity=rule.get("severity", "high"))
                    vetoes.append({"persona": p.name, "code": code, "item_id": item.get("id"), "explanation": explanation})

        # Evaluate constraint rules
        for rule in p.constraints.get("constraint", []):
            match = rule.get("match", {})
            setter = rule.get("set", {})
            # Sanity: prevent persona from changing identifiers or creating artifacts
            forbidden = set(["id", "ptr", "generated", "artifact"])
            if any(k in forbidden for k in setter.keys()):
                raise RuntimeError("persona_side_effects_disallowed")
            for item in items:
                if _matches(item, match):
                    # Record the constraint for the caller to apply deterministically
                    constraints_to_apply.append({"persona": p.name, "item_id": item.get("id"), "set": setter})
                    applied += 1
                    # Record the decision for audit (non-mutating)
                    record_decision(engine, p.name, phase, {"action": "constraint", "match": match, "set": setter})

    return {"vetoes": vetoes, "constraints_applied": applied, "constraints": constraints_to_apply}
