"""
AST to spec reconciliation report.
"""


def reconcile(ast, raw):
    """
    Reconcile AST nodes with raw spec structure.
    
    Args:
        ast: AST root node
        raw: Raw spec dict
    
    Returns:
        Dict with reconciliation report
    """
    from shieldcraft.services.spec.pointer_auditor import extract_json_pointers
    
    # Extract all AST node pointers
    ast_pointers = set()
    for node in ast.walk():
        if node.ptr:
            ast_pointers.add(node.ptr)
    
    # Extract all raw spec pointers
    raw_pointers = extract_json_pointers(raw)
    
    # Find AST nodes without raw origin
    ast_only = sorted(ast_pointers - raw_pointers)
    
    # Find raw fields not in AST
    raw_only = sorted(raw_pointers - ast_pointers)
    
    return {
        "ast_only_pointers": ast_only,
        "raw_only_pointers": raw_only,
        "ast_count": len(ast_pointers),
        "raw_count": len(raw_pointers),
        "common_count": len(ast_pointers & raw_pointers),
        "reconciliation_ok": len(ast_only) == 0 and len(raw_only) == 0
    }
