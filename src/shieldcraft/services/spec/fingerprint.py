import hashlib
import json


def compute_spec_fingerprint(spec):
    """
    Canonical fingerprint:
    sha256(canonicalized JSON spec with sorted keys)
    """
    text = json.dumps(spec, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_fingerprint_v2(spec, ast=None, invariants=None, dep_graph=None):
    """
    Deterministic spec fingerprinting v2.
    Computes hash of:
    - Canonical JSON form of spec
    - AST node ordering
    - Invariants list
    - Dependencies graph
    
    Returns: {"hash": <sha256>, "components": {...}}
    """
    components = {}
    
    # Component 1: Canonical spec
    spec_text = json.dumps(spec, sort_keys=True)
    components["spec_hash"] = hashlib.sha256(spec_text.encode("utf-8")).hexdigest()
    
    # Component 2: AST ordering
    if ast:
        ast_nodes = [node.ptr for node in ast.walk()]
        ast_text = json.dumps(ast_nodes, sort_keys=True)
        components["ast_hash"] = hashlib.sha256(ast_text.encode("utf-8")).hexdigest()
    else:
        components["ast_hash"] = "none"
    
    # Component 3: Invariants
    if invariants:
        inv_text = json.dumps(sorted(invariants), sort_keys=True)
        components["invariants_hash"] = hashlib.sha256(inv_text.encode("utf-8")).hexdigest()
    else:
        components["invariants_hash"] = "none"
    
    # Component 4: Dependencies graph
    if dep_graph:
        dep_text = json.dumps(dep_graph, sort_keys=True)
        components["dep_graph_hash"] = hashlib.sha256(dep_text.encode("utf-8")).hexdigest()
    else:
        components["dep_graph_hash"] = "none"
    
    # Combined hash
    combined = json.dumps(components, sort_keys=True)
    final_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    
    return {
        "hash": final_hash,
        "components": components
    }
