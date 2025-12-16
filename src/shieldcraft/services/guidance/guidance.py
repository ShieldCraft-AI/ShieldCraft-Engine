"""Author guidance helpers: ordering and templating for `what_is_missing_next` and messages.

This module is deterministic and data-driven (no heuristics beyond observed thresholds).
"""
from __future__ import annotations

from typing import List, Dict

# Priority map: lower number => higher priority
MISSING_PRIORITY: Dict[str, int] = {
    "sections_empty": 10,
    "invariants_empty": 20,
    "model_empty": 30,
    "missing_instructions": 40,
}


def prioritize_missing(missing: List[Dict]) -> List[Dict]:
    """Sort and deduplicate what_is_missing_next entries deterministically.

    Sorting order: by MISSING_PRIORITY (default large), then by code lexicographically.
    Duplicate codes removed, keeping first occurrence.
    """
    seen = set()
    out = []
    for item in sorted(missing, key=lambda x: (MISSING_PRIORITY.get(x.get("code"), 1000), x.get("code", ""))):
        code = item.get("code")
        if code in seen:
            continue
        seen.add(code)
        out.append(item)
    return out


def state_reason_for(conversion_state: str, missing_next: List[Dict]) -> str:
    """Return a singular state_reason code for summary.

    - If conversion_state is STRUCTURED, prefer 'structured_threshold_met'.
    - If VALID, return 'validated'.
    - Else, if there is a primary missing code, return it.
    - Fallback to conversion_state lowercased.
    """
    if conversion_state == "STRUCTURED":
        return "structured_threshold_met"
    if conversion_state == "VALID":
        return "validated"
    if missing_next:
        primary = missing_next[0].get("code")
        if primary:
            return primary
    return conversion_state.lower()


def checklist_preview_explanation(checklist_items_count: int | None, conversion_state: str) -> str:
    if checklist_items_count is None:
        return "Checklist preview not available in VALID state (checklist is authoritative)."
    return f"Checklist preview showing {checklist_items_count} items representative of current structure."
