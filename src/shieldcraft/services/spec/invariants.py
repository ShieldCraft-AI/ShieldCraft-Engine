"""
Spec-level invariants extraction.
Detects fields with keys "must", "require", "forbid" in raw spec.
"""


def extract_spec_invariants(spec):
    """
    Extract invariants from raw spec.
    
    Detects fields with keys:
    - "must": required constraint
    - "require": required constraint (alias)
    - "forbid": forbidden constraint
    
    Returns: list of invariant objects with spec_ptr + value.
    Deterministic ordering.
    """
    invariants = []
    
    def walk(obj, path=""):
        """Recursively walk spec and extract invariant fields."""
        if isinstance(obj, dict):
            for key in sorted(obj.keys()):
                new_path = f"{path}/{key}"
                value = obj[key]
                
                # Check for invariant keys
                if key in ("must", "require", "forbid", "invariant"):
                    invariant_type = "must" if key in ("must", "require", "invariant") else "forbid"
                    invariants.append({
                        "type": invariant_type,
                        "spec_ptr": new_path,
                        "constraint": value,
                        "pointer": new_path
                    })
                
                # Continue walking
                walk(value, new_path)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                new_path = f"{path}/{idx}"
                walk(item, new_path)
    
    walk(spec)
    
    # Sort deterministically by pointer
    return sorted(invariants, key=lambda x: x["spec_ptr"])
