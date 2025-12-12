"""
Self-host preview validator.
"""


def validate_preview(preview: dict) -> dict:
    """
    Validate self-host preview output.
    
    Args:
        preview: preview dict from dry-run
    
    Returns:
        dict with keys:
        - ok: bool (True if valid)
        - issues: list of issue strings
    """
    issues = []
    
    # Check modules present
    if "modules" not in preview:
        issues.append("Missing 'modules' field in preview")
    else:
        modules = preview["modules"]
        if not isinstance(modules, list):
            issues.append("'modules' field must be a list")
        elif len(modules) == 0:
            issues.append("No modules generated in preview")
    
    # Check codegen_bundle_hash exists
    if "codegen_bundle_hash" not in preview:
        issues.append("Missing 'codegen_bundle_hash' field in preview")
    else:
        bundle_hash = preview["codegen_bundle_hash"]
        if not isinstance(bundle_hash, str) or len(bundle_hash) == 0:
            issues.append("'codegen_bundle_hash' must be non-empty string")
    
    # Check lineage headers present
    if "lineage" not in preview:
        issues.append("Missing 'lineage' field in preview")
    else:
        lineage = preview["lineage"]
        if not isinstance(lineage, dict):
            issues.append("'lineage' field must be a dict")
        else:
            # Check for lineage headers
            if "headers" not in lineage:
                issues.append("Missing 'headers' in lineage")
            else:
                headers = lineage["headers"]
                if not isinstance(headers, dict):
                    issues.append("'lineage.headers' must be a dict")
    
    # Check manifest present
    if "manifest" not in preview:
        issues.append("Missing 'manifest' field in preview")
    
    # Check checklist present
    if "checklist" not in preview:
        issues.append("Missing 'checklist' field in preview")
    else:
        checklist = preview["checklist"]
        if not isinstance(checklist, list):
            issues.append("'checklist' field must be a list")
    
    return {
        "ok": len(issues) == 0,
        "issues": issues
    }
