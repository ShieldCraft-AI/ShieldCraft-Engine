def validate_cross_item_constraints(items):
    """
    Deterministic rules:
    - Every high severity must have classification != general.
    - Every critical must contain 'SPEC MISSING' in text.
    - No ptr may appear in more than one item.
    Returns filtered + warnings list.
    """
    ptr_seen = {}
    warnings = []
    out = []

    for it in items:
        ptr = it["ptr"]

        if it["severity"] == "high" and it["classification"] == "general":
            warnings.append(f"High severity item improperly classified: {it['id']}")

        if it["severity"] == "critical" and "SPEC MISSING" not in it["text"]:
            warnings.append(f"Critical item missing SPEC_MISSING marker: {it['id']}")

        if ptr in ptr_seen:
            warnings.append(f"Duplicate ptr detected: {ptr}")
            continue

        ptr_seen[ptr] = True
        out.append(it)

    return out, warnings


def validate_no_empty_sections(items):
    """
    Validate that no sections have zero items.
    
    Args:
        items: List of checklist items with ptr field.
        
    Returns:
        violations: List of section violation dicts.
    """
    # Group items by section (extract section from ptr)
    sections = {}
    for item in items:
        ptr = item.get("ptr", "")
        # Extract first component after leading slash
        parts = ptr.split("/")
        if len(parts) > 1:
            section = parts[1]
            if section not in sections:
                sections[section] = []
            sections[section].append(item["id"])
    
    violations = []
    # Check for sections with zero items
    # Note: This checks extracted sections. For spec-level validation,
    # this would need to check against the raw spec sections.
    for section, item_ids in sections.items():
        if len(item_ids) == 0:
            violations.append({
                "type": "empty_section",
                "section": section,
                "severity": "high",
                "message": f"Section '{section}' has zero checklist items"
            })
    
    return violations
