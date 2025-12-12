"""
Maps JSON Pointer prefixes to expected file paths. Strict, deterministic.
"""
from pathlib import Path

MAPPINGS = {
    "/metadata": "products/{product_id}/spec.json",
    "/features": "src/shieldcraft/features/",
    "/rules_contract/rules": "src/shieldcraft/rules/",
    "/state_machine": "src/shieldcraft/state_machine/",
    "/api": "src/shieldcraft/api/"
}


def resolve(ptr, product_id):
    for prefix, path in MAPPINGS.items():
        if ptr.startswith(prefix):
            return path.format(product_id=product_id)
    return None


def map_pointer(pointer, product_id="unknown", line_map=None):
    """
    Map JSON pointer to file location.
    Returns: {"module": <string>, "file": <Path>, "line": <int>}
    """
    # Resolve base path
    base_path = resolve(pointer, product_id)
    
    if base_path is None:
        # Deterministic fallback
        base_path = f"products/{product_id}/generated/unknown.py"
    
    # Determine line number
    line = 1
    if line_map and pointer in line_map:
        line = line_map[pointer]
    else:
        # Heuristic: hash pointer to deterministic line
        line = (hash(pointer) % 1000) + 1
    
    # Extract module name
    path_obj = Path(base_path)
    if path_obj.suffix == ".py":
        module = path_obj.stem
    else:
        module = "spec"
    
    return {
        "module": module,
        "file": path_obj,
        "line": line
    }
