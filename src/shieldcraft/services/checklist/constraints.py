def propagate_constraints(spec):
    """
    Deterministic constraint extraction.
    Produces tasks for:
    - required fields
    - conditional fields
    - structural expectations
    """
    tasks = []

    # Example: metadata requirements
    meta = spec.get("metadata", {})
    required_meta = ["product_id", "version", "owner"]
    for k in required_meta:
        if k not in meta:
            tasks.append({
                "ptr": f"/metadata/{k}",
                "text": f"Missing required metadata field: {k}",
                "value": None
            })

    # Example: architecture version must match semver
    arch = spec.get("architecture", {})
    v = arch.get("version")
    if v is not None and not isinstance(v, str):
        tasks.append({
            "ptr": "/architecture/version",
            "text": "Architecture version must be a string",
            "value": v
        })

    # Conditional rule: if agents exist, each must have type
    agents = spec.get("agents", [])
    for i, a in enumerate(agents):
        if "type" not in a:
            tasks.append({
                "ptr": f"/agents/{i}/type",
                "text": "Agent missing required 'type'",
                "value": None
            })

    return tasks
