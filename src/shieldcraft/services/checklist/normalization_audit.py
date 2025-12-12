"""
Checklist item normalization audit.
"""


def audit(items):
    """
    Audit checklist items for required fields and validity.
    
    Args:
        items: List of checklist item dicts
    
    Returns:
        Dict with missing_fields and invalid_fields lists
    """
    required_fields = ["id", "type", "ptr", "lineage_id", "severity", "classification"]
    
    missing_fields = []
    invalid_fields = []
    
    for item in items:
        item_id = item.get("id", "unknown")
        
        # Check for missing required fields
        for field in required_fields:
            if field not in item:
                missing_fields.append({
                    "item_id": item_id,
                    "missing_field": field
                })
        
        # Check field validity
        if "id" in item and not isinstance(item["id"], str):
            invalid_fields.append({
                "item_id": item_id,
                "field": "id",
                "error": "must_be_string",
                "value_type": type(item["id"]).__name__
            })
        
        if "type" in item and not isinstance(item["type"], str):
            invalid_fields.append({
                "item_id": item_id,
                "field": "type",
                "error": "must_be_string",
                "value_type": type(item["type"]).__name__
            })
        
        if "ptr" in item and not isinstance(item["ptr"], str):
            invalid_fields.append({
                "item_id": item_id,
                "field": "ptr",
                "error": "must_be_string",
                "value_type": type(item["ptr"]).__name__
            })
        
        if "severity" in item:
            valid_severities = {"critical", "high", "medium", "low"}
            if item["severity"] not in valid_severities:
                invalid_fields.append({
                    "item_id": item_id,
                    "field": "severity",
                    "error": "invalid_value",
                    "value": item["severity"],
                    "expected": list(valid_severities)
                })
    
    # Sort for determinism
    missing_fields = sorted(missing_fields, key=lambda x: (x["item_id"], x["missing_field"]))
    invalid_fields = sorted(invalid_fields, key=lambda x: (x["item_id"], x["field"]))
    
    return {
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "normalization_ok": len(missing_fields) == 0 and len(invalid_fields) == 0
    }
