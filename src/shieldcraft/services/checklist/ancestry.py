"""
Task ancestry model - tracks transformation chain for each item.
"""


def build_ancestry(items):
    """
    Build ancestry chains for checklist items.
    Includes chain_hash for each ancestry chain.
    
    Args:
        items: List of checklist items
    
    Returns:
        Dict mapping item_id to ancestry chain
    """
    import hashlib
    import json
    
    ancestry = {}
    
    for item in items:
        item_id = item.get("id")
        if not item_id:
            continue
        
        # Build transformation chain
        chain = []
        
        # Check for raw origin
        if "ptr" in item:
            chain.append("raw")
        
        # Extracted from spec
        if "lineage_id" in item:
            chain.append("extracted")
        
        # Derived task
        item_type = item.get("type", "")
        if item_type in ("fix-dependency", "resolve-invariant", "resolve-cycle", "integration"):
            chain.append("derived")
        
        # Normalized (has classification)
        if "classification" in item:
            chain.append("normalized")
        
        # Final (has all required fields)
        required = {"id", "type", "ptr", "severity"}
        if all(f in item for f in required):
            chain.append("final")
        
        # Compute chain hash
        import hashlib
        import json
        chain_str = json.dumps(chain, sort_keys=True)
        chain_hash = hashlib.sha256(chain_str.encode()).hexdigest()[:16]
        
        ancestry[item_id] = {
            "chain": chain,
            "chain_hash": chain_hash
        }
    
    return ancestry


def verify_ancestry(ancestry):
    """
    Verify ancestry chains are valid.
    
    Args:
        ancestry: Dict from build_ancestry()
    
    Returns:
        Dict with verification results
    """
    violations = []
    
    for item_id, ancestry_data in ancestry.items():
        # Handle both old (list) and new (dict) formats
        if isinstance(ancestry_data, dict):
            chain = ancestry_data.get("chain", [])
        else:
            chain = ancestry_data
        # Check for gaps
        if "final" in chain and "normalized" not in chain:
            violations.append({
                "item_id": item_id,
                "issue": "missing_normalized_stage",
                "chain": chain
            })
        
        if "normalized" in chain and "extracted" not in chain:
            violations.append({
                "item_id": item_id,
                "issue": "missing_extracted_stage",
                "chain": chain
            })
        
        # Check ordering is stable
        expected_order = ["raw", "extracted", "derived", "normalized", "final"]
        chain_positions = {stage: expected_order.index(stage) for stage in chain if stage in expected_order}
        sorted_positions = sorted(chain_positions.values())
        actual_positions = [chain_positions[stage] for stage in chain if stage in expected_order]
        
        if actual_positions != sorted_positions:
            violations.append({
                "item_id": item_id,
                "issue": "unstable_ordering",
                "chain": chain,
                "expected_order": [expected_order[p] for p in sorted_positions],
                "actual_order": [expected_order[p] for p in actual_positions]
            })
    
    return {
        "ok": len(violations) == 0,
        "violations": sorted(violations, key=lambda x: x["item_id"])
    }
