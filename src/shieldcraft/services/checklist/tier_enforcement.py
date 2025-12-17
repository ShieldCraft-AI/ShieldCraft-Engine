"""Tier enforcement for template sections.

Implements executable enforcement of the `TEMPLATE_COMPILATION_CONTRACT.md` tiering rules.

This module is deterministic, pure (no filesystem I/O), and idempotent.
"""
from typing import Dict, Any, List, Tuple

# Authoritative tier mapping (kept minimal and deterministic)
TIER_A = ["metadata", "agents", "evidence_bundle"]
TIER_B = ["determinism", "artifact_contract", "generation_mappings", "security"]
TIER_C = ["pipeline", "error_contract", "ci_contract", "observability"]


def _make_item_for_missing_section(section: str, tier: str) -> Dict[str, Any]:
    """Create a deterministic checklist item describing a missing section."""
    # Make the text intentionally trigger severity escalation rules for Tier A
    if tier == "A":
        text = f"SPEC MISSING: Missing template section: {section} (Tier {tier})"
    else:
        text = f"Missing template section: {section} (Tier {tier})"
    severity = "high" if tier == "A" else "medium"
    classification = "metadata" if section == "metadata" else ("determinism" if section == "determinism" else "compiler")
    return {
        "ptr": f"/{section}",
        "text": text,
        "meta": {
            "section": section,
            "tier": tier,
            "synthesized_default": True,
            "source": "default",
            "justification": f"safe_default_{section}",
            "justification_ptr": f"/{section}",
            "inference_type": "safe_default"
        },
        "severity": severity,
        "classification": classification,
    }


def enforce_tiers(spec: Dict[str, Any], context=None) -> List[Dict[str, Any]]:
    """Check for missing top-level sections and return checklist items to represent them.

    - For Tier A missing: produce a BLOCKER event (via context.record_event if available) and return a high severity checklist item.
    - For Tier B missing: produce a DIAGNOSTIC event and a medium severity checklist item.
    - Tier C: no checklist item.

    This function does not mutate the provided spec.
    """
    if spec is None:
        spec = {}
    missing_items = []

    def _record_event(gid, phase, outcome, message, evidence=None):
        if context is None:
            return
        try:
            context.record_event(gid, phase, outcome, message=message, evidence=evidence or {})
        except Exception:
            # Never raise from enforcement
            pass

    # Check Tier A
    for sec in sorted(TIER_A):
        if sec not in spec or spec.get(sec) is None:
            gid = f"G_TIER_A_MISSING_{sec.upper()}"
            _record_event(gid, "compilation", "BLOCKER", f"Missing Tier A section: {sec}")
            missing_items.append(_make_item_for_missing_section(sec, "A"))

    # Check Tier B
    for sec in sorted(TIER_B):
        if sec not in spec or spec.get(sec) is None:
            gid = f"G_TIER_B_MISSING_{sec.upper()}"
            _record_event(gid, "compilation", "DIAGNOSTIC", f"Missing Tier B section: {sec}")
            missing_items.append(_make_item_for_missing_section(sec, "B"))

    # Tier C intentionally ignored
    return missing_items
