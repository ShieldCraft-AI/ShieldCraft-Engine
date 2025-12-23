def check_invariants(result):
    """
    Enforce invariants:
    - evidence.hash matches bundle content.
    - lineage hashes are deterministic.
    - rollups.total == len(items)
    Returns (ok:bool, violations:list).
    """
    violations = []

    items = result.get("items", [])
    roll = result.get("rollups", {})
    if roll.get("total") != len(items):
        violations.append("rollups.total mismatch")

    evidence = result.get("evidence")
    if evidence:
        import json
        import hashlib
        rehash = hashlib.sha256(json.dumps(
            {k: v for k, v in evidence.items() if k != "hash"},
            sort_keys=True
        ).encode("utf-8")).hexdigest()
        if rehash != evidence.get("hash"):
            violations.append("evidence hash mismatch")

    lineage = result.get("lineage")
    if lineage:
        import hashlib
        import json
        base = {
            "product_id": lineage["product_id"],
            "spec_hash": lineage["spec_hash"],
            "items_hash": lineage["items_hash"]
        }
        lh = hashlib.sha256(json.dumps(base, sort_keys=True).encode("utf-8")).hexdigest()
        if lh != lineage.get("lineage_hash"):
            violations.append("lineage hash mismatch")

    return len(violations) == 0, violations
