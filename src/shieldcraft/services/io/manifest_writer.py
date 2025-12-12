import os
import json
from datetime import datetime, timezone
from .canonical_writer import write_canonical_json


def write_manifest(product_id, result):
    """
    Writes:
    products/<product_id>/manifest.json
    Contains:
    - spec_fingerprint
    - lineage
    - evidence.hash
    - rollup summary
    - invariants_ok
    - provenance (lineage_map, source_node_types)
    - spec_stats (invariants, dependencies, cycles, sections)
    """
    # Extract lineage provenance from checklist items
    checklist = result.get("checklist", {})
    items = checklist.get("items", [])
    
    lineage_provenance = {}
    unresolved_dependencies = []
    invariant_violations = []
    
    for item in items:
        if "lineage_id" in item and item.get("lineage_id"):
            item_id = item.get("id", "unknown")
            lineage_provenance[item_id] = {
                "lineage_id": item["lineage_id"],
                "source_pointer": item.get("source_pointer", "unknown"),
                "source_node_type": item.get("source_node_type", "unknown")
            }
        
        # Collect unresolved dependencies
        if item.get("type") == "fix-dependency":
            unresolved_dependencies.append({
                "item_id": item.get("id"),
                "dependency_ref": item.get("dependency_ref"),
                "severity": item.get("severity", "high")
            })
        
        # Collect invariant violations
        if item.get("type") == "resolve-invariant":
            invariant_violations.append({
                "item_id": item.get("id"),
                "invariant_type": item.get("invariant_type"),
                "constraint": item.get("invariant_constraint"),
                "severity": item.get("severity", "high")
            })
    
    # Sort for determinism
    unresolved_dependencies = sorted(unresolved_dependencies, key=lambda x: x.get("item_id", ""))
    invariant_violations = sorted(invariant_violations, key=lambda x: x.get("item_id", ""))
    
    # Compute spec stats
    from shieldcraft.services.spec.stats import compute_stats
    from shieldcraft.services.spec.lifecycle import compute_lifecycle
    spec = result.get("spec", {})
    spec_stats = compute_stats(spec, items)
    lifecycle = compute_lifecycle(spec)
    
    # Compute namespace from spec fingerprint
    spec_fp = result["preflight"]["spec_fingerprint"]
    namespace = spec_fp[:8] if spec_fp else "default"
    
    # Extract evolution if present
    spec_evolution = result.get("spec_evolution")
    evolution_summary = None
    evolution_impact = None
    if spec_evolution:
        evolution_summary = spec_evolution.get("summary", {})
        from shieldcraft.services.diff.impact import compute_evolution_impact, classify_impact
        evolution_impact = compute_evolution_impact(spec_evolution)
        evolution_impact["impact_classification"] = classify_impact(spec_evolution)
    
    # Extract reconciliation from preflight if present
    reconciliation = result.get("preflight", {}).get("ast_reconciliation")
    
    # Extract codegen bundle hash if present
    codegen_bundle_hash = result.get("generated", {}).get("codegen_bundle_hash")
    
    # Extract spec metrics if present
    spec_metrics = result.get("spec_metrics")
    
    # Extract pointer coverage from preflight
    pointer_coverage = result.get("preflight", {}).get("pointer_coverage", {})
    pointer_coverage_summary = {
        "total_pointers": pointer_coverage.get("total_pointers", 0),
        "missing_count": pointer_coverage.get("missing_count", 0),
        "ok_count": pointer_coverage.get("ok_count", 0),
        "coverage_percentage": pointer_coverage.get("coverage_percentage", 100.0)
    }
    
    data = {
        "manifest_version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "spec_fingerprint": result["preflight"]["spec_fingerprint"],
        "evidence_hash": result["evidence"]["hash"],
        "lineage": result["lineage"],
        "rollup": result["rollups"],
        "invariants_ok": result["invariants_ok"],
        "provenance": {
            "lineage_map": lineage_provenance
        },
        "unresolved_dependencies": unresolved_dependencies,
        "invariant_violations": invariant_violations,
        "spec_stats": spec_stats,
        "lifecycle": lifecycle,
        "namespace": namespace,
        "spec_evolution": evolution_summary,
        "evolution_impact": evolution_impact,
        "ast_reconciliation": reconciliation,
        "codegen_bundle_hash": codegen_bundle_hash,
        "metrics": spec_metrics,
        "pointer_coverage_summary": pointer_coverage_summary
    }
    path = f"products/{product_id}/manifest.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_canonical_json(path, data)


def write_manifest_v2(manifest, outdir, dry_run=False, codegen_bundle_hash=None):
    """
    Write canonical manifest and signature.
    
    Args:
        manifest: dict containing manifest data
        outdir: output directory path
        dry_run: If True, return manifest dict without writing files
        codegen_bundle_hash: Optional codegen bundle hash to include
        
    Returns:
        If dry_run=True, returns manifest dict
        If dry_run=False, returns None (files written)
    """
    # Add codegen_bundle_hash if provided
    if codegen_bundle_hash:
        manifest["codegen_bundle_hash"] = codegen_bundle_hash
    
    # If dry_run, just return the manifest
    if dry_run:
        return manifest
    
    # Write files
    os.makedirs(outdir, exist_ok=True)
    
    # Write manifest.json (canonical JSON)
    manifest_path = os.path.join(outdir, "manifest.json")
    write_canonical_json(manifest_path, manifest)
    
    # Compute signature
    manifest_json = json.dumps(manifest, sort_keys=True)
    import hashlib
    signature = hashlib.sha256(manifest_json.encode()).hexdigest()
    
    # Write manifest.sig
    sig_path = os.path.join(outdir, "manifest.sig")
    with open(sig_path, "w") as f:
        f.write(signature)
