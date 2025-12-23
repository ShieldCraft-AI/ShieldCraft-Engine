"""
Pointer coverage reporting.
"""


def compute_coverage(spec, items):
    """
    Compute pointer coverage statistics.

    Args:
        spec: Spec dict
        items: Checklist items

    Returns:
        Dict with coverage stats
    """
    from shieldcraft.services.spec.pointer_auditor import extract_json_pointers

    # Get all pointers from spec
    all_pointers = extract_json_pointers(spec)
    total_ptrs = len(all_pointers)

    # Get pointers covered by items
    covered_ptrs = set()
    for item in items:
        ptr = item.get("ptr", "")
        if ptr:
            covered_ptrs.add(ptr)

    # Compute uncovered
    uncovered_ptrs = all_pointers - covered_ptrs

    return {
        "total_ptrs": total_ptrs,
        "covered_ptrs": len(covered_ptrs),
        "uncovered_ptrs": len(uncovered_ptrs),
        "coverage_percentage": round(len(covered_ptrs) / total_ptrs * 100, 2) if total_ptrs > 0 else 0,
        "uncovered_list": sorted(uncovered_ptrs)
    }
