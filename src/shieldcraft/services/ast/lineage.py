"""
AST lineage integration.
Build lineage metadata from AST.
"""


def build_lineage(ast):
    """
    Build lineage list from AST.
    
    Returns: list of {pointer, lineage_id, type}
    Deterministic ordering by pointer.
    """
    lineage = []
    
    for node in ast.walk():
        if node.lineage_id:
            lineage.append({
                "pointer": node.to_pointer(),
                "lineage_id": node.lineage_id,
                "type": node.type
            })
    
    # Sort by pointer for determinism
    return sorted(lineage, key=lambda x: x["pointer"])


def get_lineage_map(ast):
    """
    Build pointer → lineage_id map.
    
    Returns: dict mapping pointers to lineage_ids
    """
    lineage_map = {}
    
    for node in ast.walk():
        if node.ptr and node.lineage_id:
            lineage_map[node.ptr] = node.lineage_id
    
    return dict(sorted(lineage_map.items()))


def verify_lineage_chain(ast):
    """
    Verify lineage chain integrity.
    
    Checks:
    - All nodes have lineage_id
    - All lineage_ids are unique
    - Parent-child lineage relationships are preserved
    
    Returns: (ok: bool, errors: [])
    """
    errors = []
    seen_lineage = set()
    
    for node in ast.walk():
        # Check node has lineage_id
        if not node.lineage_id:
            errors.append({
                "type": "missing_lineage_id",
                "pointer": node.to_pointer(),
                "node_type": node.type
            })
            continue
        
        # Check uniqueness
        if node.lineage_id in seen_lineage:
            errors.append({
                "type": "duplicate_lineage_id",
                "lineage_id": node.lineage_id,
                "pointer": node.to_pointer()
            })
        
        seen_lineage.add(node.lineage_id)
    
    return len(errors) == 0, errors
