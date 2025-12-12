def extract_dependencies(spec):
    """
    Deterministic dependency graph.
    Rules:
    - metadata.version depends on metadata.product_id
    - agents depend on architecture.version
    - api endpoints depend on schemas
    Returns list of edges: (from_ptr, to_ptr)
    """
    edges = []

    # metadata.product_id → metadata.version
    if "metadata" in spec:
        if "product_id" in spec["metadata"] and "version" in spec["metadata"]:
            edges.append((
                "/metadata/product_id",
                "/metadata/version"
            ))

    # architecture.version → agents[*]
    arch_v = spec.get("architecture", {}).get("version")
    agents = spec.get("agents", [])
    if arch_v is not None:
        for i, _ in enumerate(agents):
            edges.append((
                "/architecture/version",
                f"/agents/{i}"
            ))

    # schemas → api
    api = spec.get("api", {})
    endpoints = api.get("endpoints", [])
    for i, ep in enumerate(endpoints):
        req = ep.get("request_schema")
        res = ep.get("response_schema")
        if req:
            edges.append((f"/schemas/{req}", f"/api/endpoints/{i}"))
        if res:
            edges.append((f"/schemas/{res}", f"/api/endpoints/{i}"))

    return edges


def align_with_spec(checklist_items, spec_model):
    """
    Dependency alignment pass.
    For each checklist item, verify referenced dependencies exist in AST.
    Attach dependency_status: "ok" | "missing" | "invalid".
    """
    # Build set of valid pointers from AST
    valid_pointers = set()
    for node in spec_model.ast.walk():
        if node.ptr:
            valid_pointers.add(node.ptr)
    
    # Get spec dependencies
    spec_deps = spec_model.get_dependencies()
    spec_dep_targets = {dep["target"] for dep in spec_deps}
    
    # Process each checklist item
    aligned_items = []
    for item in checklist_items:
        # Check if item references dependencies
        item_deps = []
        
        # Look for dependency references in item
        if "dependencies" in item:
            dep_list = item["dependencies"]
            if isinstance(dep_list, list):
                item_deps = dep_list
            elif isinstance(dep_list, str):
                item_deps = [dep_list]
        
        # Look for depends_on field
        if "depends_on" in item:
            dep_ref = item["depends_on"]
            if isinstance(dep_ref, list):
                item_deps.extend(dep_ref)
            elif isinstance(dep_ref, str):
                item_deps.append(dep_ref)
        
        # Verify each dependency
        if item_deps:
            all_ok = True
            missing = []
            invalid = []
            
            for dep in item_deps:
                if dep in valid_pointers:
                    # Dependency exists in AST
                    continue
                elif dep in spec_dep_targets:
                    # Dependency declared in spec
                    continue
                else:
                    # Check if it's a section reference
                    sections = spec_model.get_sections()
                    if dep in sections or f"/{dep}" in valid_pointers:
                        continue
                    else:
                        all_ok = False
                        missing.append(dep)
            
            if all_ok:
                item["dependency_status"] = "ok"
            elif missing:
                item["dependency_status"] = "missing"
                item["missing_dependencies"] = sorted(missing)
            else:
                item["dependency_status"] = "invalid"
        else:
            # No dependencies to check
            item["dependency_status"] = "ok"
        
        aligned_items.append(item)
    
    return aligned_items
