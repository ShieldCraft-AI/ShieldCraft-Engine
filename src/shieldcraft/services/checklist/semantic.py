def compute_context_radius(item, ast):
    """
    Compute context radius for an item.
    Context radius = number of AST ancestors + siblings referenced.
    
    Args:
        item: Checklist item
        ast: AST root node
    
    Returns:
        int: Context radius value
    """
    ptr = item.get("ptr", "/")
    
    # Find node in AST
    node = ast.find(ptr) if ast and hasattr(ast, 'find') else None
    
    if not node:
        return 0
    
    # Count ancestors
    ancestors = 0
    current = node
    while hasattr(current, 'parent') and current.parent:
        ancestors += 1
        current = current.parent
    
    # Count siblings (nodes at same level)
    siblings = 0
    if hasattr(node, 'parent') and node.parent:
        parent = node.parent
        if hasattr(parent, 'children'):
            siblings = len(parent.children) - 1  # Exclude self
    
    return ancestors + siblings


def semantic_validations(spec, items=None):
    """
    Domain rules:
    - product_id lowercase snake_case
    - version matches semver
    - agents must have unique ids
    - cross-section references must be valid
    - severity must be in allowed set
    - category must be non-empty and ASCII
    - ptr must start with / if not null
    """
    tasks = []

    import re

    # product_id
    pid = spec.get("metadata", {}).get("product_id")
    if pid and not re.match(r"^[a-z0-9_]+$", pid):
        tasks.append({
            "ptr": "/metadata/product_id",
            "text": "product_id must match ^[a-z0-9_]+$",
            "value": pid
        })

    # version semver
    ver = spec.get("metadata", {}).get("version")
    if ver and not re.match(r"^\d+\.\d+\.\d+$", ver):
        tasks.append({
            "ptr": "/metadata/version",
            "text": "version must follow semver X.Y.Z",
            "value": ver
        })

    # agent id uniqueness
    agents = spec.get("agents", [])
    seen = set()
    for i, a in enumerate(agents):
        aid = a.get("id")
        if aid:
            if aid in seen:
                tasks.append({
                    "ptr": f"/agents/{i}/id",
                    "text": f"Duplicate agent id: {aid}",
                    "value": aid
                })
            seen.add(aid)
    
    # Validate items if provided
    if items:
        allowed_severities = ["low", "medium", "high", "critical"]
        for item in items:
            item_id = item.get("id", "unknown")
            
            # Check severity
            severity = item.get("severity")
            if severity and severity not in allowed_severities:
                tasks.append({
                    "ptr": item.get("ptr", "/"),
                    "text": f"Invalid severity '{severity}' for item {item_id}, must be one of {allowed_severities}",
                    "value": severity
                })
            
            # Check category
            category = item.get("category", "")
            if not category:
                tasks.append({
                    "ptr": item.get("ptr", "/"),
                    "text": f"Category must be non-empty for item {item_id}",
                    "value": category
                })
            elif not category.isascii():
                tasks.append({
                    "ptr": item.get("ptr", "/"),
                    "text": f"Category must be ASCII for item {item_id}",
                    "value": category
                })
            
            # Check ptr format
            ptr = item.get("ptr")
            if ptr is not None and ptr != "" and not ptr.startswith("/"):
                tasks.append({
                    "ptr": ptr,
                    "text": f"Pointer must start with / for item {item_id}",
                    "value": ptr
                })
    
    # Cross-section semantic checks
    # Verify that items referencing sections actually exist
    sections = spec.get("sections", [])
    section_ids = set()
    
    if isinstance(sections, list):
        for sec in sections:
            sec_id = sec.get("id")
            if sec_id:
                section_ids.add(sec_id)
    elif isinstance(sections, dict):
        section_ids = set(sections.keys())
    
    # Check all section references in the spec
    def check_section_refs(obj, path=""):
        """Recursively check for section references."""
        if isinstance(obj, dict):
            for key in obj.keys():
                value = obj[key]
                new_path = f"{path}/{key}"
                
                # Check for section reference fields
                if key in ("section", "section_ref", "section_id"):
                    if isinstance(value, str) and value not in section_ids:
                        tasks.append({
                            "ptr": new_path,
                            "text": f"Reference to missing section: {value}",
                            "value": value,
                            "meta": {"section_status": "missing"}
                        })
                    else:
                        # INTENTIONAL: Valid section reference, no action needed.
                        # Metadata will be added by subsequent processing.
                        pass
                
                # Continue recursion
                check_section_refs(value, new_path)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                new_path = f"{path}/{idx}"
                check_section_refs(item, new_path)
    
    check_section_refs(spec)
    
    # AST → checklist consistency check
    # INTENTIONAL: AST integration deferred.
    # Future: Pass AST as parameter and compare nodes to checklist coverage.
    # Current behavior: Returns all semantic tasks without AST cross-validation.
    missing_nodes = []  # Would be populated by AST comparison
    
    return tasks