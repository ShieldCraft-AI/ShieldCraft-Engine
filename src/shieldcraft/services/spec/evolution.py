"""
Spec evolution tracker - compares old and new spec versions.
"""

import json


def compute_evolution(old_spec, new_spec):
    """
    Compare old and new spec versions.
    
    Args:
        old_spec: Previous spec dict
        new_spec: Current spec dict
    
    Returns:
        Dict with evolution analysis
    """
    from shieldcraft.services.spec.pointer_auditor import extract_json_pointers
    
    old_pointers = extract_json_pointers(old_spec) if old_spec else set()
    new_pointers = extract_json_pointers(new_spec)
    
    added = sorted(new_pointers - old_pointers)
    removed = sorted(old_pointers - new_pointers)
    unchanged = sorted(old_pointers & new_pointers)
    
    # Check for changes in unchanged pointers
    changed = []
    for ptr in unchanged:
        old_val = _get_value_at_pointer(old_spec, ptr)
        new_val = _get_value_at_pointer(new_spec, ptr)
        if old_val != new_val:
            changed.append(ptr)
    
    changed = sorted(changed)
    truly_unchanged = sorted(set(unchanged) - set(changed))
    
    summary = {
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
        "unchanged_count": len(truly_unchanged),
        "total_old": len(old_pointers),
        "total_new": len(new_pointers)
    }
    
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": truly_unchanged,
        "summary": summary
    }


def _get_value_at_pointer(spec, ptr):
    """Get value at JSON pointer."""
    if not ptr or ptr == "/":
        return spec
    
    parts = ptr.lstrip("/").split("/")
    current = spec
    
    try:
        for part in parts:
            if isinstance(current, dict):
                current = current[part]
            elif isinstance(current, list):
                current = current[int(part)]
            else:
                return None
        return current
    except (KeyError, IndexError, ValueError):
        return None
