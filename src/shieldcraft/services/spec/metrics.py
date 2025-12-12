"""
Global spec metrics aggregator.
"""


def compute_metrics(spec, ast, items):
    """
    Compute comprehensive metrics for spec, AST, and checklist items.
    
    Args:
        spec: Raw spec dict
        ast: AST root node
        items: List of checklist items
    
    Returns:
        Dict with deterministic metrics
    """
    # Count sections
    sections = spec.get("sections", [])
    section_count = len(sections) if isinstance(sections, list) else 0
    
    # Count pointers
    from shieldcraft.services.spec.pointer_auditor import extract_json_pointers
    all_pointers = extract_json_pointers(spec)
    pointer_count = len(all_pointers)
    
    # Count invariants
    invariants = spec.get("invariants", [])
    invariant_count = len(invariants) if isinstance(invariants, list) else 0
    
    # Count dependencies
    dependencies = spec.get("dependencies", [])
    dependency_count = len(dependencies) if isinstance(dependencies, list) else 0
    
    # Count derived tasks
    derived_types = {"fix-dependency", "resolve-invariant", "resolve-cycle", "integration"}
    derived_task_count = sum(1 for item in items if item.get("type") in derived_types)
    
    # Count cycles
    cycle_count = sum(1 for item in items if item.get("meta", {}).get("cycle", False))
    
    # Compute coverage percentage
    covered_items = sum(1 for item in items if "ptr" in item)
    coverage_percentage = (covered_items / pointer_count * 100) if pointer_count > 0 else 0.0
    
    # Compute invariant density (invariants per section)
    invariant_density = (invariant_count / section_count) if section_count > 0 else 0.0
    
    # Compute dependency fragility (dependencies per item)
    dependency_fragility = (dependency_count / len(items)) if len(items) > 0 else 0.0
    
    # AST metrics
    ast_node_count = len(list(ast.walk())) if ast else 0
    
    return {
        "section_count": section_count,
        "pointer_count": pointer_count,
        "invariant_count": invariant_count,
        "dependency_count": dependency_count,
        "derived_task_count": derived_task_count,
        "cycle_count": cycle_count,
        "total_items": len(items),
        "ast_node_count": ast_node_count,
        "coverage_percentage": round(coverage_percentage, 2),
        "invariant_density": round(invariant_density, 2),
        "dependency_fragility": round(dependency_fragility, 2)
    }
