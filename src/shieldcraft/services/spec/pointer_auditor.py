def extract_json_pointers(spec, base=""):
    """
    Recursively extract JSON Pointer paths from spec.
    Output: set of pointer strings.
    Uses canonical DSL pointer extraction.
    """
    from shieldcraft.dsl.loader import extract_json_pointers as canonical_extract
    return canonical_extract(spec, base)


def ensure_full_pointer_coverage(ast, raw):
    """
    Ensure all raw spec pointers have corresponding AST nodes.
    
    Args:
        ast: The parsed AST with nodes.
        raw: The raw spec dictionary.
        
    Returns:
        Report with {missing: [...], ok: [...]}.
    """
    # Derive all pointers from raw spec
    all_pointers = extract_json_pointers(raw)
    
    # Get all AST node paths
    ast_pointers = set()
    if hasattr(ast, 'walk'):
        for node in ast.walk():
            if node.ptr:
                ast_pointers.add(node.ptr)
    elif isinstance(ast, dict):
        ast_nodes = ast.get("nodes", [])
        for node in ast_nodes:
            if isinstance(node, dict) and node.get("ptr"):
                ast_pointers.add(node["ptr"])
            elif hasattr(node, 'ptr') and node.ptr:
                ast_pointers.add(node.ptr)
    
    # Determine missing and ok
    missing = sorted(list(all_pointers - ast_pointers))
    ok = sorted(list(all_pointers & ast_pointers))
    
    return {
        "missing": missing,
        "ok": ok,
        "count": {
            "missing": len(missing),
            "ok": len(ok)
        }
    }


def compute_coverage(pointers, checklist_items):
    """
    Determine which pointers have no checklist coverage.
    Returns:
        uncovered: set,
        covered: set
    """
    covered = set(it["ptr"] for it in checklist_items)
    uncovered = pointers - covered
    return uncovered, covered


def check_unreachable_pointers(ast, raw):
    """
    Check for raw pointers not found in AST.
    Supports canonical and legacy spec formats.
    Returns list of unreachable pointer paths.
    """
    # Extract all pointers from raw spec
    raw_pointers = extract_json_pointers(raw)
    
    # Extract all pointers from AST
    ast_pointers = set()
    if hasattr(ast, 'walk'):
        for node in ast.walk():
            if hasattr(node, 'ptr') and node.ptr:
                ast_pointers.add(node.ptr)
    
    # Canonical specs may have additional metadata keys - filter them out
    if isinstance(raw, dict):
        canonical_metadata_keys = {'canonical', 'canonical_spec_hash', 'float_precision'}
        metadata = raw.get('metadata', {})
        for key in canonical_metadata_keys:
            ptr = f"/metadata/{key}"
            if ptr in raw_pointers and ptr not in ast_pointers:
                raw_pointers.discard(ptr)
    
    # Find pointers in raw but not in AST
    unreachable = raw_pointers - ast_pointers
    
    # Sort for deterministic output
    return sorted(unreachable)


def ensure_full_pointer_coverage_old(raw, ast):
    """
    Return pointers in AST not represented in raw spec.
    This is the inverse check - AST pointers not in raw.
    Note: Function signature changed - raw first, then ast for consistency.
    """
    # Extract all pointers from raw spec
    raw_pointers = extract_json_pointers(raw)
    
    # Extract all pointers from AST
    ast_pointers = set()
    if hasattr(ast, 'walk'):
        for node in ast.walk():
            if node.ptr:
                ast_pointers.add(node.ptr)
    elif isinstance(ast, dict):
        ast_nodes = ast.get("nodes", [])
        for node in ast_nodes:
            if isinstance(node, dict) and node.get("ptr"):
                ast_pointers.add(node["ptr"])
            elif hasattr(node, 'ptr') and node.ptr:
                ast_pointers.add(node.ptr)
    
    # Find pointers in AST but not in raw
    uncovered_ast_pointers = ast_pointers - raw_pointers
    
    # Sort for deterministic output
    return sorted(uncovered_ast_pointers)



def pointer_audit(raw, ast, checklist_items):
    """
    Comprehensive pointer audit.
    Returns dict with coverage info and uncovered AST pointers.
    Includes locality warnings for pointers crossing section boundaries.
    """
    raw_pointers = extract_json_pointers(raw)
    uncovered_raw, covered = compute_coverage(raw_pointers, checklist_items)
    unreachable = check_unreachable_pointers(ast, raw)
    uncovered_ast = ensure_full_pointer_coverage_old(raw, ast)
    
    # Check pointer locality constraints
    locality_warnings = []
    
    # Get all top-level sections
    sections_data = raw.get("sections", [])
    top_level_sections = set()
    
    if isinstance(sections_data, list):
        for idx, sec in enumerate(sections_data):
            top_level_sections.add(f"/sections/{idx}")
    elif isinstance(sections_data, dict):
        for key in sections_data.keys():
            top_level_sections.add(f"/sections/{key}")
    
    # Check each item for cross-section pointer references
    for item in checklist_items:
        item_ptr = item.get("ptr", "")
        
        # Determine item's top-level section
        item_section = None
        for sec in top_level_sections:
            if item_ptr.startswith(sec):
                item_section = sec
                break
        
        if not item_section:
            continue
        
        # Check if item references pointers from different sections
        # Look for dependency references or cross-references
        for ref_field in ["depends_on", "requires", "references"]:
            refs = item.get(ref_field, [])
            if isinstance(refs, list):
                for ref in refs:
                    if isinstance(ref, str) and ref.startswith("/sections/"):
                        # Check if ref is from different top-level section
                        ref_section = None
                        for sec in top_level_sections:
                            if ref.startswith(sec):
                                ref_section = sec
                                break
                        
                        if ref_section and ref_section != item_section:
                            locality_warnings.append({
                                "item_id": item.get("id", "unknown"),
                                "item_ptr": item_ptr,
                                "item_section": item_section,
                                "reference": ref,
                                "reference_section": ref_section,
                                "severity": "medium"
                            })
    
    # Check pointer range references (e.g., array[*])
    pointer_range_errors = []
    
    for item in checklist_items:
        item_ptr = item.get("ptr", "")
        
        # Look for wildcard array references
        if "[*]" in item_ptr or "/*" in item_ptr:
            # Extract base pointer (before the wildcard)
            if "[*]" in item_ptr:
                base_ptr = item_ptr.split("[*]")[0]
            else:
                base_ptr = item_ptr.split("/*")[0]
            
            # Check if base pointer points to an array in raw spec
            try:
                parts = [p for p in base_ptr.split("/") if p]
                current = raw
                
                for part in parts:
                    if isinstance(current, dict):
                        current = current.get(part)
                    elif isinstance(current, list):
                        try:
                            idx = int(part)
                            current = current[idx]
                        except (ValueError, IndexError):
                            current = None
                            break
                    else:
                        current = None
                        break
                
                # Verify current is an array
                if current is None:
                    pointer_range_errors.append({
                        "item_id": item.get("id", "unknown"),
                        "pointer": item_ptr,
                        "error": "base_pointer_not_found",
                        "base_pointer": base_ptr
                    })
                elif not isinstance(current, list):
                    pointer_range_errors.append({
                        "item_id": item.get("id", "unknown"),
                        "pointer": item_ptr,
                        "error": "not_an_array",
                        "base_pointer": base_ptr
                    })
                elif len(current) == 0:
                    pointer_range_errors.append({
                        "item_id": item.get("id", "unknown"),
                        "pointer": item_ptr,
                        "error": "empty_array",
                        "base_pointer": base_ptr
                    })
            except Exception as e:
                pointer_range_errors.append({
                    "item_id": item.get("id", "unknown"),
                    "pointer": item_ptr,
                    "error": "validation_error",
                    "message": str(e)
                })
    
    # Check pointer shape validity
    pointer_shape_errors = []
    
    for item in checklist_items:
        item_ptr = item.get("ptr", "")
        
        # Check for double slashes
        if "//" in item_ptr:
            pointer_shape_errors.append({
                "item_id": item.get("id", "unknown"),
                "pointer": item_ptr,
                "error": "double_slash"
            })
        
        # Check for trailing slash
        if item_ptr.endswith("/") and item_ptr != "/":
            pointer_shape_errors.append({
                "item_id": item.get("id", "unknown"),
                "pointer": item_ptr,
                "error": "trailing_slash"
            })
        
        # Check for invalid characters
        import re
        if not re.match(r'^(/[a-zA-Z0-9_\-]+)*/?$', item_ptr) and item_ptr != "/":
            # Allow numbers for array indices
            if not re.match(r'^(/[a-zA-Z0-9_\-]+(/[0-9]+)?)*/?$', item_ptr):
                pointer_shape_errors.append({
                    "item_id": item.get("id", "unknown"),
                    "pointer": item_ptr,
                    "error": "invalid_characters"
                })
    
    return {
        "uncovered_raw_pointers": sorted(uncovered_raw),
        "covered_pointers": sorted(covered),
        "unreachable_pointers": unreachable,
        "uncovered_ast_pointers": uncovered_ast,
        "locality_warnings": sorted(locality_warnings, key=lambda x: x.get("item_id", "")),
        "pointer_range_errors": sorted(pointer_range_errors, key=lambda x: x.get("item_id", "")),
        "pointer_shape_errors": sorted(pointer_shape_errors, key=lambda x: x.get("item_id", ""))
    }
