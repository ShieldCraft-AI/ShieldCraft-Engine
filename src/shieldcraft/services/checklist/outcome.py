"""Canonical outcome derivation for checklists.

Authoritative single function to derive canonical primary outcome from checklist and gate events.

Primary precedence: REFUSAL > BLOCKER > ACTION > DIAGNOSTIC

This module must be deterministic and not rely on persona annotations to set outcomes.
"""
from typing import Dict, List, Tuple, Any


def _agg_confidence_level(items: List[Dict[str, Any]]) -> str:
    """Aggregate confidence across checklist items.

    Rules (deterministic):
    - If any item has confidence 'high' -> 'high'
    - Else if any item has confidence 'medium' -> 'medium'
    - Else -> 'low'
    """
    confs = [((it.get('confidence') or '').lower()) for it in items if isinstance(it, dict)]
    if any(c == 'high' for c in confs):
        return 'high'
    if any(c == 'medium' for c in confs):
        return 'medium'
    return 'low'


def derive_primary_outcome(checklist: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Deterministically derive primary outcome and metadata.

    Args:
        checklist: dict with key 'items' -> list of checklist items
        events: list of gate event dicts; persona-origin events are ignored for outcome derivation

    Returns:
        Dict with keys: primary_outcome (str), refusal (bool), blocking_reasons (List[str]), confidence_level (str)
    """
    # Defensive inputs
    items = (checklist.get('items') if checklist and isinstance(checklist.get('items'), list) else [])
    evs = events or []
    # Ensure events are dicts to avoid attribute errors and make function total
    evs = [e for e in evs if isinstance(e, dict)]

    # Exclude persona-origin events from primary outcome calculation
    non_persona_events = [e for e in evs if not e.get('persona_id')]

    # Extract normalized outcomes (presence checks only; order-independent)
    normalized = [((e.get('outcome') or '')).upper() for e in non_persona_events]

    # Blocking reasons: messages from REFUSAL or BLOCKER events (deterministic order by gate_id then message)
    brs = []
    for e in sorted([e for e in non_persona_events if (e.get('outcome') or '').upper() in ('REFUSAL', 'BLOCKER')], key=lambda x: (x.get('gate_id') or '', str(x.get('message') or ''))):
        msg = e.get('message') or e.get('gate_id') or ''
        brs.append(msg)

    # Determine primary_outcome per precedence
    if any(o == 'REFUSAL' for o in normalized):
        primary = 'REFUSAL'
        refusal = True
    elif any(o == 'BLOCKER' for o in normalized):
        primary = 'BLOCKED'
        refusal = False
    else:
        # ACTION if any actionable items
        # Actionable heuristic: confidence not 'low' (existing fields only)
        confs = [((it.get('confidence') or '').lower()) for it in items if isinstance(it, dict)]
        has_actionable = any(c in ('high', 'medium') for c in confs)
        if has_actionable:
            primary = 'ACTION'
            refusal = False
        else:
            primary = 'DIAGNOSTIC'
            refusal = False

    confidence_level = _agg_confidence_level(items)

    return {
        'primary_outcome': primary,
        'refusal': refusal,
        'blocking_reasons': brs,
        'confidence_level': confidence_level,
    }
