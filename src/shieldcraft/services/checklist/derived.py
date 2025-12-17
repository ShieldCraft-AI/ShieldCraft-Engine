from .idgen import synthesize_id
import json


def _make_deterministic_id(parent_id: str, task_type: str, payload: dict) -> str:
    """
    Generate deterministic ID using sha256 of parent_id + type + canonicalized payload.
    Format: <parent_id>::derived::<type>::<sha8>
    """
    from shieldcraft.util.canonical_digest import digest_text
    
    # Canonicalize payload
    canonical_payload = json.dumps(payload, sort_keys=True)
    
    # Combine and hash
    combined = f"{parent_id}::{task_type}::{canonical_payload}"
    hash_full = digest_text(combined)
    
    # Truncate to 8 hex chars
    hash_short = hash_full[:8]
    
    return f"{parent_id}::derived::{task_type}::{hash_short}"


def infer_tasks(item):
    """
    Infer derived tasks from a normalized checklist item.
    Returns synthetic tasks based on missing fields, dependencies, bootstrap category, etc.
    Enhanced to support module and bootstrap types.
    All derived tasks inherit lineage_id and spec_ptr from parent.
    Uses deterministic ID generation.
    """
    derived = []
    ptr = item.get("ptr", "")
    classification = item.get("classification", "general")
    category = item.get("category", "general")
    item_type = item.get("type", "default")
    base_id = item.get("id", "unknown")
    
    # Inherit parent provenance
    parent_lineage_id = item.get("lineage_id")
    parent_spec_ptr = item.get("source_pointer", ptr)
    parent_node_type = item.get("source_node_type", "unknown")
    value = item.get("value", {}) or {}
    
    # Module-type derived tasks
    if item_type == "module":
        module_name = item.get('name', 'unknown')
        
        # Derive test task
        test_payload = {"type": "test", "module": module_name}
        derived.append({
            "id": _make_deterministic_id(base_id, "module_test", test_payload),
            "ptr": f"{ptr}/test",
            "text": f"Generate tests for module {module_name}",
            "type": "module_test",
            "category": category,
            "classification": classification,
            "severity": "medium",
            "source_pointer": parent_spec_ptr,
            "source_section": item.get("source_section", "unknown"),
            "lineage_id": parent_lineage_id,
            "source_node_type": parent_node_type,
            "meta": {"parent_id": base_id, "derived_type": "module_test", "source": "derived", "derived_from": base_id, "justification": "derived_module_test", "justification_ptr": parent_spec_ptr, "inference_type": "structural"}
        })
        
        # Derive imports task
        imports_payload = {"type": "imports", "module": module_name}
        derived.append({
            "id": _make_deterministic_id(base_id, "module_imports", imports_payload),
            "ptr": f"{ptr}/imports",
            "text": f"Generate imports for module {module_name}",
            "type": "module_imports",
            "category": category,
            "classification": classification,
            "severity": "low",
            "source_pointer": parent_spec_ptr,
            "source_section": item.get("source_section", "unknown"),
            "lineage_id": parent_lineage_id,
            "source_node_type": parent_node_type,
                "meta": {"parent_id": base_id, "derived_type": "module_imports", "source": "derived", "derived_from": base_id, "justification": "derived_module_imports", "justification_ptr": parent_spec_ptr, "inference_type": "structural"}
        })
        
        # Derive init structure task
        init_payload = {"type": "init", "module": module_name}
        derived.append({
            "id": _make_deterministic_id(base_id, "module_init", init_payload),
            "ptr": f"{ptr}/init",
            "text": f"Generate __init__ structure for module {module_name}",
            "type": "module_init",
            "category": category,
            "classification": classification,
            "severity": "low",
            "source_pointer": parent_spec_ptr,
            "source_section": item.get("source_section", "unknown"),
            "lineage_id": parent_lineage_id,
            "source_node_type": parent_node_type,
                "meta": {"parent_id": base_id, "derived_type": "module_init", "source": "derived", "derived_from": base_id, "justification": "derived_module_init", "justification_ptr": parent_spec_ptr, "inference_type": "structural"}
        })
    
    # Bootstrap derived tasks
    if category == "bootstrap":
        bootstrap_payload = {"type": "impl", "ptr": ptr}
        derived.append({
            "id": _make_deterministic_id(base_id, "bootstrap_impl", bootstrap_payload),
            "ptr": ptr,
            "text": "Generate bootstrap component",
            "type": "bootstrap_impl",
            "category": "bootstrap",
            "classification": "bootstrap",
            "severity": "low",
            "source_pointer": parent_spec_ptr,
            "source_section": item.get("source_section", "unknown"),
            "lineage_id": parent_lineage_id,
            "source_node_type": parent_node_type,
                "meta": {"parent_id": base_id, "derived_type": "bootstrap_impl", "source": "derived", "derived_from": base_id, "justification": "derived_bootstrap_impl", "justification_ptr": parent_spec_ptr, "inference_type": "structural"}
        })
        # Add verification task for bootstrap components
        verify_payload = {"type": "verify", "ptr": ptr}
        derived.append({
            "id": _make_deterministic_id(base_id, "bootstrap_verify", verify_payload),
            "ptr": f"{ptr}/verify",
            "text": "Verify bootstrap component",
            "type": "bootstrap_verify",
            "category": "bootstrap",
            "classification": "bootstrap",
            "severity": "low",
            "source_pointer": parent_spec_ptr,
            "source_section": item.get("source_section", "unknown"),
            "lineage_id": parent_lineage_id,
            "source_node_type": parent_node_type,
                "meta": {"parent_id": base_id, "derived_type": "bootstrap_verify", "source": "derived", "derived_from": base_id, "justification": "derived_bootstrap_verify", "justification_ptr": parent_spec_ptr, "inference_type": "structural"}
        })
    
    # Missing dependency derived tasks
    if item_type == "fix-dependency" or "depends_on" in item or "dependencies" in item:
        depends_on = item.get("depends_on", []) + item.get("dependencies", [])
        if isinstance(depends_on, list):
            for dep in depends_on:
                dep_payload = {"type": "fix_dep", "dependency": dep}
                derived.append({
                    "id": _make_deterministic_id(base_id, "fix-dependency", dep_payload),
                    "ptr": f"{ptr}/dependencies/{dep}",
                    "text": f"Fix missing dependency: {dep}",
                    "type": "fix-dependency",
                    "category": category,
                    "classification": "fix-dependency",
                    "severity": "high",
                    "dependency_ref": dep,
                    "source_pointer": parent_spec_ptr,
                    "source_section": item.get("source_section", "unknown"),
                    "lineage_id": parent_lineage_id,
                    "source_node_type": parent_node_type,
                    "meta": {"parent_id": base_id, "derived_type": "fix-dependency", "dependency": dep, "source": "derived", "derived_from": base_id, "justification": "derived_fix_dependency", "inference_type": "structural"}
                })
    # Also detect dependencies inside value payload
    if isinstance(value, dict) and "dependencies" in value:
        deps = value.get("dependencies", [])
        if isinstance(deps, list):
            for dep in deps:
                dep_payload = {"type": "fix_dep", "dependency": dep}
                derived.append({
                    "id": _make_deterministic_id(base_id, "fix-dependency", dep_payload),
                    "ptr": f"{ptr}/dependencies/{dep}",
                    "text": f"Fix missing dependency: {dep}",
                    "type": "fix-dependency",
                    "category": category,
                    "classification": "fix-dependency",
                    "severity": "high",
                    "dependency_ref": dep,
                    "source_pointer": parent_spec_ptr,
                    "source_section": item.get("source_section", "unknown"),
                    "lineage_id": parent_lineage_id,
                    "source_node_type": parent_node_type,
                    "meta": {"parent_id": base_id, "derived_type": "fix-dependency", "dependency": dep, "source": "derived", "derived_from": base_id, "justification": "derived_fix_dependency", "inference_type": "structural"}
                })
    
    # Invariant violation derived tasks

    # Metadata missing field derived tasks (e.g., product_id, version)
    if ptr == "/metadata" and isinstance(value, dict):
        if "product_id" not in value:
            payload = {"type": "set", "field": "product_id"}
            derived.append({
                "id": _make_deterministic_id(base_id, "set_product_id", payload),
                "ptr": f"{ptr}/product_id",
                "text": "Set product_id in metadata",
                "type": "set-metadata",
                "category": "meta",
                "classification": "meta",
                "severity": "critical",
                "source_pointer": parent_spec_ptr,
                "source_section": item.get("source_section", "unknown"),
                "lineage_id": parent_lineage_id,
                "source_node_type": parent_node_type,
                "meta": {
                    "parent_id": base_id,
                    "derived_from": base_id,
                    "derived_type": "set_product_id",
                    "source": "derived",
                    "justification": "missing_metadata_field:product_id",
                    "justification_ptr": f"{ptr}/product_id",
                    "inference_type": "structural",
                    "tier": "A"
                }
            })
        if "version" not in value:
            payload = {"type": "set", "field": "version"}
            derived.append({
                "id": _make_deterministic_id(base_id, "set_version", payload),
                "ptr": f"{ptr}/version",
                "text": "Set version in metadata",
                "type": "set-metadata",
                "category": "meta",
                "classification": "meta",
                "severity": "critical",
                "source_pointer": parent_spec_ptr,
                "source_section": item.get("source_section", "unknown"),
                "lineage_id": parent_lineage_id,
                "source_node_type": parent_node_type,
                "meta": {
                    "parent_id": base_id,
                    "derived_from": base_id,
                    "derived_type": "set_version",
                    "source": "derived",
                    "justification": "missing_metadata_field:version",
                    "justification_ptr": f"{ptr}/version",
                    "inference_type": "structural",
                    "tier": "A"
                }
            })
    # legacy and structured invariant reporting
    invs = item.get("meta", {}).get("invariant_violations", []) or []
    if item.get("invariant_violation") or item_type == "resolve-invariant" or (isinstance(invs, list) and len(invs) > 0):
        # Prefer explicit invariant_id if present in meta; fallback to item field
        if isinstance(invs, list) and len(invs) > 0 and isinstance(invs[0], dict):
            invariant_id = invs[0].get("id", item.get("invariant_id", "unknown"))
        else:
            invariant_id = item.get("invariant_id", "unknown")
        inv_payload = {"type": "resolve_inv", "invariant": invariant_id}
        derived.append({
            "id": _make_deterministic_id(base_id, "resolve-invariant", inv_payload),
            "ptr": f"{ptr}/invariant/{invariant_id}",
            "text": f"Resolve invariant violation: {invariant_id}",
            "type": "resolve-invariant",
            "category": category,
            "classification": "resolve-invariant",
            "severity": "high",
            "invariant_id": invariant_id,
            "invariant_type": item.get("invariant_type", "unknown"),
            "invariant_constraint": item.get("invariant_constraint"),
            "source_pointer": parent_spec_ptr,
            "source_section": item.get("source_section", "unknown"),
            "lineage_id": parent_lineage_id,
            "source_node_type": parent_node_type,
            "meta": {"parent_id": base_id, "derived_type": "resolve-invariant", "invariant_id": invariant_id, "derived_from": base_id, "justification": f"resolve_invariant:{invariant_id}", "inference_type": "structural"}
        })
    
    return sorted(derived, key=lambda x: (x["ptr"], x.get("id", "")))



