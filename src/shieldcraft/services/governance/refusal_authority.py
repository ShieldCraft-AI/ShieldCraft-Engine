"""Refusal authority mapping and helpers.

Provides authoritative mapping of REFUSAL gates to refusal authorities and a
helper to record refusal events with explicit refusal metadata attached.
"""
from typing import Optional, Dict, Any

# Authoritative gate -> authority mapping (complete for known REFUSAL gates used here)
REFUSAL_AUTHORITY_MAP = {
    "G1_ENGINE_READINESS_FAILURE": "infrastructure",
    "G2_GOVERNANCE_PRESENCE_CHECK": "governance",
    "G3_REPO_SYNC_VERIFICATION": "infrastructure",
    "G5_VALIDATION_TYPE_GATES": "governance",
    "G7_PERSONA_VETO": "persona",
    "G8_TEST_ATTACHMENT_CONTRACT": "governance",
    "G12_PERSONA_VETO_ENFORCEMENT": "persona",
    "G14_SELFHOST_INPUT_SANDBOX": "selfhost",
    "G15_DISALLOWED_SELFHOST_ARTIFACT": "selfhost",
    "G16_MINIMALITY_INVARIANT_FAILED": "governance",
    "G17_EXECUTION_CYCLE_DETECTED": "infrastructure",
    "G18_MISSING_ARTIFACT_PRODUCER": "governance",
    "G19_PRIORITY_VIOLATION_DETECTED": "governance",
    "G20_QUALITY_GATE_FAILED": "quality",
}


def get_authority_for_gate(gate_id: str) -> str:
    if gate_id in REFUSAL_AUTHORITY_MAP:
        return REFUSAL_AUTHORITY_MAP[gate_id]
    raise ValueError(f"Unknown refusal gate: {gate_id}; must map to an authority")


def record_refusal_event(context, gate_id: str, phase: str, message: Optional[str] = None,
                         evidence: Optional[Dict[str, Any]] = None, trigger: Optional[str] = None,
                         scope: Optional[str] = None, justification: Optional[str] = None) -> None:
    """Record a REFUSAL event with explicit refusal metadata attached.

    The event's evidence will include an entry `refusal` with keys:
        authority, trigger, scope, justification
    This helper enforces that a known authority exists for the gate and attaches
    the refusal metadata deterministically.
    """
    if evidence is None:
        evidence = {}
    # Resolve authority (raises if gate not mapped)
    authority = get_authority_for_gate(gate_id)

    refusal_meta = {
        "authority": authority,
        "trigger": trigger or "unspecified",
        "scope": scope or "run",
        "justification": justification or "unspecified",
    }

    # Attach refusal metadata inside evidence as structured data
    ev = dict(evidence) if isinstance(evidence, dict) else {}
    ev.setdefault("refusal", {}).update(refusal_meta)

    # Record the REFUSAL event via the provided context
    try:
        context.record_event(gate_id, phase, "REFUSAL", message=message, evidence=ev)
    except Exception:
        # If recording fails, raise to make the missing metadata visible upstream
        raise
