"""Deterministic, minimal conversion path generator.

Produces a single-step conversion path from current state -> next_state with
an ordered list of blocking requirements and an estimated effort.
"""
from __future__ import annotations

from typing import List, Dict, Any
from .guidance import prioritize_missing


NEXT_STATE: Dict[str, str] = {
    "ACCEPTED": "CONVERTIBLE",
    "CONVERTIBLE": "STRUCTURED",
    "STRUCTURED": "VALID",
    "VALID": "READY",
}


CODE_SUGGESTIONS: Dict[str, str] = {
    "model_empty": "Add a non-empty 'model' object.",
    "missing_instructions": "Add at least one 'instruction' to the 'instructions' section.",
    "invariants_empty": "Add a non-empty 'invariants' list.",
    "sections_empty": "Add the required DSL sections (e.g., metadata, model, instructions).",
}


GATE_SUGGESTIONS: Dict[str, str] = {
    "tests_attached": "Attach passing tests (add test refs to the spec).",
    "determinism_replay": "Provide a determinism snapshot and ensure it replays identically.",
    "spec_fuzz_stability": "Stabilize spec elements so fuzz variants are consistent.",
}


def _positive_for_missing(item: Dict[str, Any]) -> str:
    code = item.get("code")
    if not code:
        return item.get("message", "Provide required content to progress to the next state.")
    if code in CODE_SUGGESTIONS:
        return CODE_SUGGESTIONS[code]
    # Fallback to message or a generic positive phrasing
    if item.get("message"):
        return item.get("message")
    return f"Address '{code}' to meet the next state requirements."


def build_conversion_path(conversion_state: str | None,
                          missing_next: List[Dict[str, Any]] | None, readiness: Dict[str, Any] | None) -> Dict[str, Any]:
    """Return a deterministic conversion_path dict.

    - `conversion_state`: current state (string) e.g. 'CONVERTIBLE'
    - `missing_next`: list of missing items (may be empty)
    - `readiness`: readiness report dict (may be None)
    """
    cur = (conversion_state or "ACCEPTED").upper()
    next_state = NEXT_STATE.get(cur, "CONVERTIBLE")

    missing = prioritize_missing(missing_next or [])

    blocking_requirements: List[Dict[str, str]] = []

    # If moving to READY, derive blockers from readiness report
    if next_state == "READY" and readiness:
        results = readiness.get("results", {})
        # Blocking gates where ok == False and blocking == True
        gates = [g for g, r in sorted(results.items()) if isinstance(results.get(g), dict)
                 and not results[g].get("ok") and results[g].get("blocking")]
        for g in gates:
            suggestion = GATE_SUGGESTIONS.get(g, f"Address readiness gate: {g}.")
            blocking_requirements.append({"code": g, "suggestion": suggestion})

    # Otherwise, convert missing_next items into positive suggestions
    if not blocking_requirements:
        for item in missing:
            code = item.get("code")
            suggestion = _positive_for_missing(item)
            blocking_requirements.append({"code": code or "unspecified", "suggestion": suggestion})

    # Anti-no-machine: never emit empty path for non-READY
    if not blocking_requirements and next_state != "READY":
        # Provide a single generic positive next step
        if next_state == "STRUCTURED":
            suggestion = "Add metadata.product_id or a non-empty 'model' or at least one 'instruction'."
        elif next_state == "VALID":
            suggestion = "Address semantic strictness requirements (add required sections such as 'invariants' or 'model')."
        else:
            suggestion = f"Take steps to reach {next_state} by following the checklist guidance."
        blocking_requirements = [{"code": "guidance_generic", "suggestion": suggestion}]

    # Deterministic estimated effort
    cnt = len(blocking_requirements)
    if cnt <= 1:
        effort = "low"
    elif cnt == 2:
        effort = "medium"
    else:
        effort = "high"

    # Ensure ordering is deterministic (already sorted by prioritize_missing or gates order)
    return {
        "current_state": cur,
        "next_state": next_state,
        "blocking_requirements": blocking_requirements,
        "estimated_effort": effort,
    }
