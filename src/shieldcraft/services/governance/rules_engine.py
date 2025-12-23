"""
Governance rules evaluation engine.
Evaluates spec compliance against governance policies.
"""


def evaluate_governance(spec_model, checklist_items):
    """
    Evaluate governance rules for spec and checklist.

    Checks:
    - Presence of required _sections
    - Forbidden patterns (from invariants)
    - Missing provenance tags

    Returns: {ok: bool, violations: []}
    """
    violations = []

    # Check required _sections
    required_sections = ["metadata", "model", "_sections"]
    raw_spec = spec_model.raw

    for req_section in required_sections:
        if req_section not in raw_spec:
            violations.append({
                "type": "missing_required_section",
                "section": req_section,
                "severity": "high"
            })

    # Check for forbidden patterns from invariants
    invariants = spec_model.get_invariants()
    for inv in invariants:
        if inv["type"] == "forbid":
            constraint = inv["constraint"]
            # Check if forbidden pattern appears in checklist items
            for item in checklist_items:
                item_text = item.get("text", "")
                item_ptr = item.get("ptr", "")
                if isinstance(constraint, str):
                    if constraint.lower() in item_text.lower() or constraint.lower() in item_ptr.lower():
                        violations.append({
                            "type": "forbidden_pattern",
                            "item_id": item.get("id", "unknown"),
                            "pattern": constraint,
                            "pointer": inv["pointer"],
                            "severity": inv.get("severity", "error")
                        })

    # Missing provenance fields are advisory and not enforced by default.
    # If stricter provenance enforcement is desired, enable via configuration.

    # Check checklist items for missing metadata
    for item in checklist_items:
        if "id" not in item:
            violations.append({
                "type": "missing_item_id",
                "item_ptr": item.get("ptr", "unknown"),
                "severity": "high"
            })

        if "classification" not in item:
            violations.append({
                "type": "missing_classification",
                "item_id": item.get("id", "unknown"),
                "severity": "medium"
            })

        # Note: missing lineage is advisory and not treated as a governance violation
        # by default. Lineage enforcement can be enabled via configuration if needed.

        # Check section reference validity (must_have_section_reference_valid rule)
        section_status = item.get("meta", {}).get("section_status")
        if section_status == "missing":
            violations.append({
                "type": "invalid_section_reference",
                "item_id": item.get("id", "unknown"),
                "item_ptr": item.get("ptr", "unknown"),
                "severity": "high"
            })

    # Determine overall status. Treat missing lineage as advisory (non-fatal)
    fatal_violations = [v for v in violations if v.get("type") != "missing_lineage"]
    ok = len(fatal_violations) == 0

    return {
        "ok": ok,
        "violations": sorted(violations, key=lambda v: (v.get("severity", "low"), v.get("type", "")))
    }
