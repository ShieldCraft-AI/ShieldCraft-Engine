import json
from ..spec.schema_validator import validate_spec_against_schema
from ..spec.pointer_auditor import extract_json_pointers, compute_coverage, ensure_full_pointer_coverage
from ..ast.shape_validator import validate_shape
from ..generator.contract_verifier import verify_generation_contract
from ..spec.fingerprint import compute_spec_fingerprint
from ..ast.lineage import verify_lineage_chain


def run_preflight(spec, schema, checklist_items):
    """
    Perform preflight:
    1. schema validation
    2. pointer extraction
    3. coverage audit
    4. contract verification
    5. governance evaluation
    6. lineage verification

    Returns:
      {
        "schema_valid": bool,
        "schema_errors": [...],
        "uncovered_ptrs": [...],
        "contract_ok": bool,
        "contract_violations": [...],
        "governance_ok": bool,
        "governance_violations": [...],
        "lineage_ok": bool,
        "lineage_violations": [...]
      }
    """
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.services.spec.model import SpecModel
    from shieldcraft.services.governance.rules_engine import evaluate_governance
    from shieldcraft.services.ast.lineage import build_lineage
    
    valid_schema, schema_errors = validate_spec_against_schema(spec, schema)
    ptrs = extract_json_pointers(spec)
    uncovered, _ = compute_coverage(ptrs, checklist_items)
    ok_contract, violations = verify_generation_contract(spec, checklist_items, uncovered)
    
    # Build SpecModel for governance evaluation
    # Check if spec is already a SpecModel (from canonical loader)
    if isinstance(spec, SpecModel):
        spec_model = spec
        ast = spec_model.ast
        spec_fingerprint = spec_model.fingerprint
        spec_raw = spec_model.raw
    else:
        ast_builder = ASTBuilder()
        ast = ast_builder.build(spec)
        spec_fingerprint = compute_spec_fingerprint(spec)
        spec_model = SpecModel(spec, ast, spec_fingerprint)
        spec_raw = spec
    
    # Run pointer coverage enforcement with canonical support
    from shieldcraft.services.spec.pointer_auditor import check_unreachable_pointers
    pointer_coverage = ensure_full_pointer_coverage(ast, spec_raw)
    unreachable_pointers = check_unreachable_pointers(ast, spec_raw)
    
    # Record missing pointers in preflight output format
    missing_pointers = pointer_coverage.get("missing", [])
    contract_ok_final = ok_contract and (len(missing_pointers) == 0) and (len(unreachable_pointers) == 0)
    
    # Run governance evaluation
    governance_result = evaluate_governance(spec_model, checklist_items)
    
    # Verify lineage chain (use AST object, not lineage_data list)
    lineage_ok, lineage_violations = verify_lineage_chain(ast)
    
    # Detect unresolved dependencies
    unresolved_dependencies = []
    for item in checklist_items:
        depends_on = item.get("depends_on", [])
        if isinstance(depends_on, list):
            for dep_ref in depends_on:
                # Check if dependency is resolved in checklist
                resolved = any(
                    it.get("id") == dep_ref or it.get("ptr") == dep_ref
                    for it in checklist_items
                )
                if not resolved:
                    unresolved_dependencies.append({
                        "item_id": item.get("id", "unknown"),
                        "dependency_ref": dep_ref,
                        "severity": "high"
                    })
    
    dependency_ok = len(unresolved_dependencies) == 0
    
    # Run mapping inspector
    from shieldcraft.services.codegen.mapping_inspector import inspect as inspect_mappings
    codegen_targets = inspect_mappings(checklist_items, strict=False)
    
    # Validate AST shape
    ast_shape_result = validate_shape(ast)
    
    # Run normalization audit
    from shieldcraft.services.checklist.normalization_audit import audit as normalization_audit
    norm_audit = normalization_audit(checklist_items)
    
    # Run AST reconciliation
    from shieldcraft.services.ast.reconcile import reconcile
    reconciliation = reconcile(ast, spec)

    return {
        "schema_valid": valid_schema,
        "schema_errors": schema_errors,
        "uncovered_ptrs": sorted(uncovered),
        "contract_ok": contract_ok_final,
        "contract_violations": violations,
        "spec_fingerprint": spec_fingerprint,
        "pointer_coverage": pointer_coverage,
        "governance_ok": governance_result["ok"],
        "governance_violations": governance_result["violations"],
        "lineage_ok": lineage_ok,
        "lineage_violations": lineage_violations,
        "dependency_ok": dependency_ok,
        "unresolved_dependencies": unresolved_dependencies,
        "codegen_targets": codegen_targets,
        "ast_shape_ok": ast_shape_result["shape_ok"],
        "ast_shape_errors": ast_shape_result["shape_errors"],
        "normalization_ok": norm_audit["normalization_ok"],
        "normalization_audit": norm_audit,
        "ast_reconciliation": reconciliation
    }

