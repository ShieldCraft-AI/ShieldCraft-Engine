"""Test manifest structure and schema compliance."""
import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError


def test_manifest_structure():
    """Test that generated manifest has correct structure."""
    # Create minimal test data
    from shieldcraft.services.io.manifest_writer import write_manifest
    
    product_id = "test_manifest"
    
    # Minimal result structure
    result = {
        "preflight": {
            "spec_fingerprint": "test_fingerprint_abc123",
            "pointer_coverage": {
                "total_pointers": 10,
                "missing_count": 0,
                "ok_count": 10,
                "coverage_percentage": 100.0
            }
        },
        "evidence": {
            "hash": "evidence_hash_def456"
        },
        "lineage": {},
        "rollups": {},
        "invariants_ok": True,
        "checklist": {
            "items": []
        },
        "spec": {
            "metadata": {
                "product_id": product_id
            }
        },
        "spec_metrics": {
            "section_count": 3,
            "pointer_count": 10,
            "invariant_count": 2,
            "coverage_percentage": 100.0,
            "invariant_density": 0.2,
            "dependency_fragility": 0.1
        },
        "generated": {
            "codegen_bundle_hash": "codegen_hash_ghi789"
        }
    }
    
    # Write manifest
    write_manifest(product_id, result)
    
    # Read generated manifest
    manifest_path = Path(f"products/{product_id}/manifest.json")
    assert manifest_path.exists(), "Manifest file not created"
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Validate structure
    assert "manifest_version" in manifest, "manifest_version missing"
    assert "timestamp" in manifest, "timestamp missing"
    assert "spec_fingerprint" in manifest, "spec_fingerprint missing"
    assert "pointer_coverage_summary" in manifest, "pointer_coverage_summary missing"
    assert "metrics" in manifest, "metrics missing"
    
    # Cleanup
    import shutil
    shutil.rmtree("products", ignore_errors=True)


def test_manifest_with_bootstrap_spec():
    """Test manifest generation with bootstrap spec example."""
    from shieldcraft.services.io.manifest_writer import write_manifest
    import json
    
    # Load bootstrap spec
    bootstrap_spec_path = Path(__file__).parent.parent.parent / "examples" / "selfhost" / "bootstrap_spec.json"
    
    if not bootstrap_spec_path.exists():
        pytest.skip("Bootstrap spec not found")
    
    with open(bootstrap_spec_path) as f:
        spec = json.load(f)
    
    product_id = spec.get("metadata", {}).get("product_id", "test_bootstrap")
    
    # Create minimal result with bootstrap spec
    result = {
        "preflight": {
            "spec_fingerprint": "bootstrap_fingerprint",
            "pointer_coverage": {
                "total_pointers": len(spec.get("items", [])),
                "missing_count": 0,
                "ok_count": len(spec.get("items", [])),
                "coverage_percentage": 100.0
            }
        },
        "evidence": {
            "hash": "bootstrap_evidence_hash"
        },
        "lineage": {},
        "rollups": {},
        "invariants_ok": True,
        "checklist": {
            "items": spec.get("items", [])
        },
        "spec": spec,
        "spec_metrics": {
            "section_count": len(spec.get("sections", [])),
            "pointer_count": len(spec.get("items", [])),
            "invariant_count": len(spec.get("invariants", [])),
            "coverage_percentage": 100.0,
            "invariant_density": 0.2,
            "dependency_fragility": 0.1
        },
        "generated": {
            "codegen_bundle_hash": "bootstrap_codegen_hash"
        }
    }
    
    # Write manifest
    write_manifest(product_id, result)
    
    # Verify manifest created
    manifest_path = Path(f"products/{product_id}/manifest.json")
    assert manifest_path.exists()
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Verify bootstrap-specific fields
    assert "manifest_version" in manifest
    assert "spec_fingerprint" in manifest
    
    # Cleanup
    import shutil
    shutil.rmtree(f"products/{product_id}", ignore_errors=True)


def test_manifest_validates_against_schema():
    """Test that manifest validates against manifest.schema.json."""
    # Load schema
    schema_path = Path(__file__).parent.parent.parent / "src/shieldcraft/dsl/schema/manifest.schema.json"
    with open(schema_path) as f:
        schema = json.load(f)
    
    # Create test manifest
    manifest = {
        "manifest_version": "1.0",
        "spec_fingerprint": "test_fp_123",
        "timestamp": "2025-12-12T00:00:00Z",
        "pointer_coverage_summary": {
            "total_pointers": 5,
            "missing_count": 0,
            "ok_count": 5,
            "coverage_percentage": 100.0
        }
    }
    
    # Validate
    try:
        validate(instance=manifest, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Manifest validation failed: {e.message}")


def test_manifest_pointer_coverage_summary():
    """Test that pointer_coverage_summary has required fields."""
    from shieldcraft.services.io.manifest_writer import write_manifest
    
    product_id = "test_coverage"
    
    result = {
        "preflight": {
            "spec_fingerprint": "fp_123",
            "pointer_coverage": {
                "total_pointers": 15,
                "missing_count": 2,
                "ok_count": 13,
                "coverage_percentage": 86.67
            }
        },
        "evidence": {"hash": "ev_hash"},
        "lineage": {},
        "rollups": {},
        "invariants_ok": True,
        "checklist": {"items": []},
        "spec": {"metadata": {"product_id": product_id}}
    }
    
    write_manifest(product_id, result)
    
    manifest_path = Path(f"products/{product_id}/manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    summary = manifest["pointer_coverage_summary"]
    
    assert "total_pointers" in summary
    assert "missing_count" in summary
    assert "ok_count" in summary
    assert "coverage_percentage" in summary
    
    assert summary["total_pointers"] == 15
    assert summary["missing_count"] == 2
    assert summary["ok_count"] == 13
    
    # Cleanup
    import shutil
    shutil.rmtree("products", ignore_errors=True)


def test_manifest_metrics_structure():
    """Test that metrics field has expected structure."""
    from shieldcraft.services.io.manifest_writer import write_manifest
    
    product_id = "test_metrics"
    
    result = {
        "preflight": {
            "spec_fingerprint": "fp_metrics",
            "pointer_coverage": {
                "total_pointers": 10,
                "missing_count": 0,
                "ok_count": 10,
                "coverage_percentage": 100.0
            }
        },
        "evidence": {"hash": "ev_hash"},
        "lineage": {},
        "rollups": {},
        "invariants_ok": True,
        "checklist": {"items": []},
        "spec": {"metadata": {"product_id": product_id}},
        "spec_metrics": {
            "section_count": 5,
            "pointer_count": 20,
            "invariant_count": 3,
            "coverage_percentage": 95.0,
            "invariant_density": 0.15,
            "dependency_fragility": 0.2
        }
    }
    
    write_manifest(product_id, result)
    
    manifest_path = Path(f"products/{product_id}/manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    assert "metrics" in manifest
    metrics = manifest["metrics"]
    
    expected_fields = ["section_count", "pointer_count", "invariant_count"]
    for field in expected_fields:
        assert field in metrics, f"Missing metrics field: {field}"
    
    # Cleanup
    import shutil
    shutil.rmtree("products", ignore_errors=True)
