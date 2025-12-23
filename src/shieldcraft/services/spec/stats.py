"""
Spec statistics computation.
Computes deterministic statistics about spec and checklist.
"""


def compute_stats(spec, items):
    """
    Compute deterministic statistics.

    Args:
        spec: Spec dict
        items: Checklist items list

    Returns:
        Dict with:
        - invariant_count: number of invariants
        - dependency_count: number of dependencies
        - cycle_count: number of cycles detected
        - section_count: number of sections
        - item_count: total items
        - type_breakdown: counts per item type
    """
    # Count sections
    sections = spec.get("sections", [])
    section_count = len(sections)

    # Count items by type
    item_count = len(items)
    type_breakdown = {}

    # Count specific features
    invariant_count = 0
    dependency_count = 0
    cycle_count = 0

    for item in items:
        item_type = item.get("type", "task")
        type_breakdown[item_type] = type_breakdown.get(item_type, 0) + 1

        # Count invariants
        if item.get("invariants_from_spec"):
            invariant_count += len(item["invariants_from_spec"])

        # Count dependencies
        depends_on = item.get("depends_on", [])
        if depends_on:
            if isinstance(depends_on, list):
                dependency_count += len(depends_on)
            else:
                dependency_count += 1

        # Count cycles
        if item.get("meta", {}).get("cycle"):
            cycle_count += 1

    # Sort type breakdown for determinism
    type_breakdown = dict(sorted(type_breakdown.items()))

    return {
        "invariant_count": invariant_count,
        "dependency_count": dependency_count,
        "cycle_count": cycle_count,
        "section_count": section_count,
        "item_count": item_count,
        "type_breakdown": type_breakdown
    }
