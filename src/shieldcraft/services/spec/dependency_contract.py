def validate_dependencies(spec):
    """
    Enforce:
    - features referencing rules must reference existing rule IDs
    - no unknown rule categories
    Returns (ok, violations)
    """
    violations = []
    rules = {r["id"]: r for r in spec.get("rules_contract", {}).get("rules", [])}
    cats = set(spec.get("rules_contract", {}).get("categories", []))

    feats = spec.get("features", {})
    for fname, f in feats.items():
        for rid in f.get("rules", []):
            if rid not in rules:
                violations.append(f"feature {fname} references missing rule {rid}")
        for rid in f.get("rules", []):
            rc = rules.get(rid)
            if rc and rc.get("category") not in cats:
                violations.append(f"rule {rid} has unknown category {rc.get('category')}")

    return len(violations)==0, violations
