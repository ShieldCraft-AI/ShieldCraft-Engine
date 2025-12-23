"""
Codegen mapping inspector - determines codegen targets for checklist items.
"""


def inspect(items, strict=False):
    """
    Inspect items and determine codegen targets.

    Args:
        items: List of checklist items
        strict: If True, raise on unmapped required items

    Returns:
        List of {item_id, target, ptr} dicts
    """
    targets = []
    unmapped_required = []

    for item in items:
        item_id = item.get("id", "unknown")
        item_type = item.get("type", "task")
        ptr = item.get("ptr", "")

        # Determine target
        target = "none"

        if item_type == "fix-dependency":
            target = "fix-dependency"
        elif item_type == "resolve-invariant":
            target = "resolve-invariant"
        elif item_type == "resolve-cycle":
            target = "resolve-cycle"
        elif item_type == "integration":
            target = "integration"
        elif "module" in item.get("source_node_type", "").lower():
            target = "module"
        elif item.get("meta", {}).get("is_module"):
            target = "module"

        targets.append({
            "item_id": item_id,
            "target": target,
            "ptr": ptr
        })

        # Check if required but unmapped
        if strict and target == "none":
            if item.get("required", False) or item.get("severity") == "critical":
                unmapped_required.append(item_id)

    if strict and unmapped_required:
        raise ValueError(f"Unmapped required items: {unmapped_required}")

    # Sort for determinism
    return sorted(targets, key=lambda x: x["item_id"])
