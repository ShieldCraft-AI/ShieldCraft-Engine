def classify_item(item):
    """
    Deterministic classifier with enhanced global classification.

    Returns class based on multiple factors:
    1. Special types (fix-dependency, resolve-invariant, resolve-cycle)
    2. Bootstrap indicators
    3. Module indicators
    4. Dependencies
    5. Invariants
    6. Pointer-based classification (backward compatible)
    7. Default to core
    """
    item_type = item.get("type", "task")

    # Fixed classification by type - highest priority
    if item_type == "fix-dependency":
        return "dependency"

    if item_type == "resolve-invariant":
        return "invariant"

    if item_type == "resolve-cycle":
        return "dependency"

    if item_type == "integration":
        return "integration"

    # Check for bootstrap indicators
    if item.get("bootstrap", False):
        return "bootstrap"

    if item.get("meta", {}).get("bootstrap", False):
        return "bootstrap"

    source_section = item.get("source_section", "")
    if source_section in ["metadata", "model", "sections"]:
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

    # Pointer-based classification (backward compatible)
    ptr = item.get("ptr", "")
    if ptr:
        if "metadata" in ptr:
            return "metadata"
        if "runtime" in ptr:
            return "runtime"
        if "api" in ptr:
            return "api"
        if "features" in ptr:
            return "features"
        if "determinism" in ptr:
            return "determinism"
        if "zero_cost" in ptr:
            return "zero_cost"
        if "performance" in ptr:
            return "performance"
        if "ci" in ptr:
            return "ci"

    # Default to core
    return "core"


def classify_type(item):
    """
    Classify item into one of four types:
    - structural: meta items (id starts with 'meta::')
    - behavioral: derived items
    - governance: invariant category items
    - bootstrap: bootstrap category items

    Returns: str (one of the four types)
    """
    item_id = item.get("id", "")
    category = item.get("category", "")
    origin = item.get("origin", {})

    # Check ID prefix
    if item_id.startswith("meta::"):
        return "structural"

    # Check category
    if category == "invariant":
        return "governance"

    if category == "bootstrap":
        return "bootstrap"

    # Check origin
    if origin.get("source") == "derived":
        return "behavioral"

    # Default to structural
    return "structural"


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
