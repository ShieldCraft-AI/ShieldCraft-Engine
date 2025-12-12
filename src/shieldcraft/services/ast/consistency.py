"""
AST consistency checker - verifies alignment between raw spec and AST.
"""


def verify(ast, raw_spec):
    """
    Check consistency between DSL and AST.
    Returns list of issues found.
    """
    issues = []
    
    # Check 1: Every raw field appears in AST
    raw_pointers = _collect_raw_pointers(raw_spec)
    ast_pointers = {node.ptr for node in ast.walk()}
    
    for ptr in raw_pointers:
        if ptr not in ast_pointers:
            issues.append({
                "type": "missing_in_ast",
                "pointer": ptr,
                "message": f"Raw spec field at '{ptr}' not found in AST"
            })
    
    # Check 2: No AST node missing a pointer
    for node in ast.walk():
        if node.ptr is None:
            issues.append({
                "type": "missing_pointer",
                "node": str(node),
                "message": f"AST node missing pointer: {node}"
            })
    
    # Check 3: Reference resolution matches
    ref_issues = _verify_references(ast, raw_spec)
    issues.extend(ref_issues)
    
    return issues


def _collect_raw_pointers(obj, path="", result=None):
    """Recursively collect all JSON pointers from raw spec."""
    if result is None:
        result = set()
    
    result.add(path if path else "/")
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}/{key}" if path != "/" else f"/{key}"
            _collect_raw_pointers(value, child_path, result)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            child_path = f"{path}/{idx}"
            _collect_raw_pointers(item, child_path, result)
    
    return result


def _verify_references(ast, raw_spec):
    """Verify that reference resolution matches between AST and raw spec."""
    issues = []
    
    # Collect all reference fields from both
    ast_refs = set()
    for node in ast.walk():
        if isinstance(node.value, dict):
            val = node.value.get("value", {})
            if isinstance(val, dict) and "ref" in val:
                ast_refs.add(val["ref"])
    
    raw_refs = _collect_refs(raw_spec)
    
    # Check for mismatches
    for ref in ast_refs:
        if ref not in raw_refs:
            issues.append({
                "type": "reference_mismatch",
                "ref": ref,
                "message": f"Reference '{ref}' in AST but not in raw spec"
            })
    
    for ref in raw_refs:
        if ref not in ast_refs:
            issues.append({
                "type": "reference_mismatch",
                "ref": ref,
                "message": f"Reference '{ref}' in raw spec but not in AST"
            })
    
    return issues


def _collect_refs(obj, result=None):
    """Collect all 'ref' fields from raw spec."""
    if result is None:
        result = set()
    
    if isinstance(obj, dict):
        if "ref" in obj:
            result.add(obj["ref"])
        for value in obj.values():
            _collect_refs(value, result)
    elif isinstance(obj, list):
        for item in obj:
            _collect_refs(item, result)
    
    return result
