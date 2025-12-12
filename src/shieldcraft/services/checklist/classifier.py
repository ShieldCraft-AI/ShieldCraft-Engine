"""
Classification engine for checklist items.
Assigns deterministic class labels based on item properties.
"""


def classify_item(item):
    """
    Classify checklist item based on type, dependencies, invariants, severity.
    
    Args:
        item: Checklist item dict with type, dependencies, invariants, etc.
    
    Returns:
        Classification string: "core" | "dependency" | "invariant" | "bootstrap" | "module"
    """
    item_type = item.get("type", "task")
    
    # Fixed classification by type
    if item_type == "fix-dependency":
        return "dependency"
    
    if item_type == "resolve-invariant":
        return "invariant"
    
    if item_type == "resolve-cycle":
        return "dependency"
    
    # Check for bootstrap indicators
    if item.get("bootstrap", False):
        return "bootstrap"
    
    if item.get("meta", {}).get("bootstrap", False):
        return "bootstrap"
    
    # Check for module indicators
    if "module" in item.get("source_node_type", "").lower():
        return "module"
    
    if item.get("meta", {}).get("is_module", False):
        return "module"
    
    # Check for dependency indicators
    depends_on = item.get("depends_on", [])
    if depends_on:
        return "dependency"
    
    # Check for invariant indicators
    invariants = item.get("invariants_from_spec", [])
    if invariants:
        return "invariant"
    
    # Default to core
    return "core"


def classify_items(items):
    """
    Classify all items in checklist.
    
    Args:
        items: List of checklist items
    
    Returns:
        Dict mapping item_id to classification
    """
    classifications = {}
    for item in items:
        item_id = item.get("id")
        if item_id:
            classifications[item_id] = classify_item(item)
    
    return classifications
