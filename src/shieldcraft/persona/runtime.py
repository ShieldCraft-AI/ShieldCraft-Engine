from typing import Any, Dict
from shieldcraft.persona.contract import ensure_allowed
from shieldcraft.persona.decision_record import record_decision


class PersonaRuntime:
    """Constrained persona evaluator for decision points.

    Personas can `annotate`, `veto`, `suggest`, or `rank` options. They
    are NOT allowed to generate artifacts. All outputs are recorded via
    `record_decision` for auditability.
    """

    def __init__(self, engine):
        self.engine = engine

    def evaluate(self, persona, action: str, phase: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ensure_allowed(persona, action)

        # Deterministic decision derivation: base on persona name + action + inputs canonicalized
        # For simplicity, create a stable decision structure.
        if action == "annotate":
            decision = {
                "action": "annotate", "message": inputs.get(
                    "message", ""), "severity": inputs.get(
                    "severity", "info")}
        elif action == "veto":
            decision = {
                "action": "veto", "code": inputs.get(
                    "code", "veto"), "explanation": inputs.get(
                    "explanation", {})}
        elif action == "suggest":
            # Suggest a single deterministic option by hashing input key names
            opts = inputs.get("options", [])
            chosen = opts[0] if opts else None
            decision = {"action": "suggest", "suggestion": chosen}
        elif action == "rank":
            opts = inputs.get("options", [])
            # Deterministic ranking: sort lexicographically
            ranked = sorted(opts)
            decision = {"action": "rank", "ranked": ranked}
        else:
            raise ValueError(f"unsupported_persona_action:{action}")

        # Record decision for audit and enforce non-authority: decisions only
        record_decision(self.engine, persona.name, phase, decision)
        return decision
