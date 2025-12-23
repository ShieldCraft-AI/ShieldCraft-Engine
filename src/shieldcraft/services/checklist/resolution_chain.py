"""
Resolution chain builder for derived tasks.
"""


def build_chain(items):
    """
    Build resolution chains for derived tasks.

    Args:
        items: List of checklist items

    Returns:
        Dict mapping item_id to resolution chain
    """
    chains = {}

    # Build pointer→item mapping
    ptr_to_item = {}
    for item in items:
        ptr = item.get("ptr")
        if ptr:
            ptr_to_item[ptr] = item

    # For each derived task, trace back to source
    for item in items:
        item_id = item.get("id")
        item_type = item.get("type", "task")

        # Check if it's a derived task
        if item_type in ("fix-dependency", "resolve-invariant", "resolve-cycle", "integration"):
            chain = _trace_chain(item, ptr_to_item)
            chains[item_id] = chain

    return chains


def _trace_chain(item, ptr_to_item, visited=None):
    """
    Trace resolution chain back to original source.

    Returns list of pointers in chain order.
    """
    if visited is None:
        visited = set()

    item_id = item.get("id")

    # Prevent cycles
    if item_id in visited:
        return []

    visited.add(item_id)

    chain = []

    # Add current pointer
    ptr = item.get("ptr", "")
    if ptr:
        chain.append(ptr)

    # Check for dependencies
    depends_on = item.get("depends_on", [])
    if isinstance(depends_on, list):
        for dep_ref in depends_on:
            # Find referenced item
            if dep_ref in ptr_to_item:
                dep_item = ptr_to_item[dep_ref]
                dep_chain = _trace_chain(dep_item, ptr_to_item, visited)
                chain.extend(dep_chain)

    return chain


def verify_chains(chains):
    """
    Verify resolution chains are valid.

    Args:
        chains: Dict from build_chain()

    Returns:
        Dict with verification results
    """
    violations = []

    for item_id, chain in chains.items():
        # Check for loops (duplicates in chain)
        if len(chain) != len(set(chain)):
            violations.append({
                "item_id": item_id,
                "issue": "chain_contains_loop",
                "chain_length": len(chain)
            })

        # Check deterministic length (should be reasonable)
        if len(chain) > 100:
            violations.append({
                "item_id": item_id,
                "issue": "chain_too_long",
                "chain_length": len(chain)
            })

    return {
        "ok": len(violations) == 0,
        "violations": violations
    }
