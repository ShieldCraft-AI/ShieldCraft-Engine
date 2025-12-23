def cross_section_checks(spec, items=None):
    """
    Deterministic cross-field rules:
    - If agents exist, architecture must exist
    - If API exists, schemas must exist
    - All items with deps must reference items in same or earlier sections
    """
    tasks = []
    violations = []

    if spec.get("agents") and "architecture" not in spec:
        tasks.append({
            "ptr": "/architecture",
            "text": "Agents require architecture section",
            "value": None
        })

    if "api" in spec and "schemas" not in spec:
        tasks.append({
            "ptr": "/schemas",
            "text": "API requires schemas section",
            "value": None
        })

    # Validate dependency ordering if items provided
    if items:
        # Build item index by id
        item_index = {item["id"]: item for item in items}
        # Build section order map
        section_order_map = {}
        for idx, item in enumerate(items):
            section_order_map[item["id"]] = idx

        # Check each item's dependencies
        for item in items:
            item_id = item.get("id")
            deps = item.get("deps", [])
            if not deps:
                continue

            item_position = section_order_map.get(item_id, 0)

            for dep_id in deps:
                if dep_id not in item_index:
                    # Dependency doesn't exist
                    violations.append({
                        "type": "cross_section_order",
                        "item": item_id,
                        "dep": dep_id,
                        "reason": "dependency not found"
                    })
                else:
                    dep_position = section_order_map.get(dep_id, 0)
                    if dep_position > item_position:
                        # Dependency comes after dependent (invalid order)
                        violations.append({
                            "type": "cross_section_order",
                            "item": item_id,
                            "dep": dep_id,
                            "reason": "dependency must come before dependent"
                        })

    # Legacy consumers expect a simple list of generated tasks
    # If caller provided `items`, return detailed structure including violations
    if items:
        return {"tasks": tasks, "violations": violations}

    # Legacy callers who expect a simple list of tasks will call without
    # the `items` parameter; return the list in that case.
    return tasks
