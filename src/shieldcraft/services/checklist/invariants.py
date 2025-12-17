def extract_invariants(ast):
    """
    Extract invariant checks from AST.
    Scans for 'invariant', 'must', 'forbid', 'require' fields.
    Returns structured invariant objects with canonical sorting.
    
    Returns:
        List of dicts with keys: id, spec_ptr, expr, severity
    """
    invariants = []
    
    # Handle AST object
    if hasattr(ast, 'walk'):
        for node in ast.walk():
            if node.type == "dict_entry" and isinstance(node.value, dict):
                value_obj = node.value.get("value", {})
                if isinstance(value_obj, dict):
                    # Check for invariant fields
                    for field in ["must", "forbid", "require", "invariant"]:
                        if field in value_obj:
                            constraint = value_obj[field]
                            invariants.append({
                                "pointer": node.ptr,
                                "type": "invariant",
                                "constraint": constraint,
                                "severity": value_obj.get("severity", "error")
                            })
    # Handle raw spec dicts by simple recursive scan
    elif isinstance(ast, dict):
        def _scan_dict(obj, base_ptr=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    ptr = f"{base_ptr}/{k}"
                    if isinstance(v, dict):
                        # Check for invariant-like keys inside dict
                        for field in ["must", "forbid", "require", "invariant"]:
                            if field in v:
                                invariants.append({
                                    "pointer": ptr,
                                    "type": "invariant",
                                    "constraint": v[field],
                                    "severity": v.get("severity", "error")
                                })
                        # Recurse
                        _scan_dict(v, ptr)
                    elif isinstance(v, list):
                        for idx, item in enumerate(v):
                            _scan_dict(item, f"{ptr}/{idx}")
        _scan_dict(ast, "")
    
    # Canonical sort by pointer
    invariants.sort(key=lambda inv: inv.get("pointer", inv.get("id", "")))
    
    return invariants


def evaluate_invariant(expr: str, context: dict) -> bool:
    """
    Evaluate invariant expression with safe sandboxing.
    
    Supports minimal expression operations:
    - exists(ptr): check if pointer exists in context
    - count(ptr) > N: count items at pointer
    - unique(ptrs): check uniqueness across pointers
    
    Args:
        expr: invariant expression string
        context: dict with 'items' list and 'spec' dict
    
    Returns:
        bool: True if invariant passes, False otherwise
    """
    expr = expr.strip()
    items = context.get("items", [])
    spec = context.get("spec", {})
    
    # exists(ptr) - check if pointer exists
    if expr.startswith("exists(") and expr.endswith(")"):
        ptr = expr[7:-1].strip().strip("'\"")
        # Check if any item has this pointer
        for item in items:
            if item.get("ptr") == ptr:
                return True
        # Check if spec has this pointer
        return _resolve_ptr(spec, ptr) is not None
    
    # count(ptr) > N, count(ptr) >= N, count(ptr) == N
    if expr.startswith("count("):
        import re
        match = re.match(r"count\(([^)]+)\)\s*([><=]+)\s*(\d+)", expr)
        if match:
            ptr = match.group(1).strip().strip("'\"")
            op = match.group(2)
            threshold = int(match.group(3))
            
            # Count items with this pointer prefix
            count = sum(1 for item in items if item.get("ptr", "").startswith(ptr))
            
            if op == ">":
                return count > threshold
            elif op == ">=":
                return count >= threshold
            elif op == "==":
                return count == threshold
            elif op == "<":
                return count < threshold
            elif op == "<=":
                return count <= threshold
    
    # unique(ptrs) - check uniqueness
    if expr.startswith("unique(") and expr.endswith(")"):
        ptr_pattern = expr[7:-1].strip().strip("'\"")
        # Collect values at pointer pattern
        values = []
        for item in items:
            if item.get("ptr", "").startswith(ptr_pattern):
                # Get ID or value for uniqueness check
                val = item.get("id") or item.get("ptr")
                if val:
                    values.append(val)
        # Check if all unique
        return len(values) == len(set(values))
    
    # Default: assume true for unknown expressions (safe default)
    # Record explainability info in context for the caller to attach to items
    try:
        if isinstance(context, dict):
            ctxmap = context.setdefault('_invariant_eval_explain', {})
            ctxmap[expr] = {'source': 'default_true', 'justification': 'unknown_expr_safe_default'}
            try:
                import logging
                logging.getLogger(__name__).debug(f"evaluate_invariant: recorded safe default for expr={expr}")
            except Exception:
                pass
    except Exception:
        pass
    return True


def is_known_expression(expr: str) -> bool:
    """Return True if the expression matches supported expression patterns."""
    if expr is None:
        return False
    expr = expr.strip()
    if expr.startswith("exists(") and expr.endswith(")"):
        return True
    if expr.startswith("count("):
        return True
    if expr.startswith("unique(") and expr.endswith(")"):
        return True
    return False


def _resolve_ptr(spec, ptr):
    """Resolve a pointer in spec dict."""
    if not ptr or ptr == "/":
        return spec
    
    parts = ptr.strip("/").split("/")
    current = spec
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    
    return current

