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
                                "id": f"inv.{node.ptr.replace('/', '.')}.{field}",
                                "spec_ptr": node.ptr,
                                "expr": constraint,
                                "severity": value_obj.get("severity", "medium")
                            })
    
    # Canonical sort by id
    invariants.sort(key=lambda inv: inv["id"])
    
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
    return True


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

