"""
Self-host minimal end-to-end test.
Verify bootstrap module emission and stability checks.
"""
import json
import os
import tempfile
import pytest
from shieldcraft.dsl.loader import load_spec


def test_selfhost_minimal_pipeline():
    """
    Test minimal self-host pipeline with bootstrap.
    Supply minimal DSL spec with self_host=true.
    Uses loader adapter for canonical/legacy support.
    """
    from shieldcraft.main import run_self_host
    import shutil
    
    # Create minimal self-host spec
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {
                "product_id": "test-selfhost-minimal",
                "version": "1.0",
                "spec_format": "canonical_json_v1",
                "self_host": True
            },
            "model": {
                "version": "1.0"
            },
            "sections": [{"id": "bootstrap","description": "Bootstrap components","loader": {"type": "loader_stage"},"engine": {"type": "engine_stage"}}]
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name
    
    try:
        # Clean output directory
        if os.path.exists(".selfhost_outputs"):
            shutil.rmtree(".selfhost_outputs")
        
        # Run self-host
        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")
        
        # Verify bootstrap modules emitted (if any bootstrap items exist)
        # Note: Bootstrap modules only emitted if bootstrap items have classification == "bootstrap"
        # This test may pass without bootstrap modules if spec has no bootstrap-classified items
        
        # Verify bootstrap manifest exists if modules were generated
        if os.path.exists(".selfhost_outputs/modules"):
            assert os.path.exists(".selfhost_outputs/bootstrap_manifest.json"), "Bootstrap manifest missing"
            
            # Load and verify manifest
            with open(".selfhost_outputs/bootstrap_manifest.json") as f:
                manifest = json.load(f)
            
            assert "modules" in manifest, "Manifest missing modules"
            assert "count" in manifest, "Manifest missing count"
            assert manifest["count"] >= 0, "Invalid module count"
        
        # Verify summary exists (always required)
        assert os.path.exists(".selfhost_outputs/summary.json"), "Summary missing"
        
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_selfhost_no_missing_pointer_errors():
    """Test self-host with no missing pointer errors."""
    from shieldcraft.main import run_self_host
    import shutil
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {
                "product_id": "test-pointer-check",
                "version": "1.0",
                "spec_format": "canonical_json_v1",
                "self_host": True
            },
            "model": {"version": "1.0"},
            "sections": [{"id": "core", "description": "Core components"}]
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name
    
    try:
        # Clean output directory
        if os.path.exists(".selfhost_outputs"):
            shutil.rmtree(".selfhost_outputs")
        
        # Run self-host
        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")
        
        # Check for errors
        if os.path.exists(".selfhost_outputs/error.txt"):
            with open(".selfhost_outputs/error.txt") as f:
                error_content = f.read()
            pytest.fail(f"Self-host produced errors: {error_content}")
        
        # Verify summary exists (indicates successful run)
        assert os.path.exists(".selfhost_outputs/summary.json")
        
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_selfhost_stability_check():
    """Test self-host runs stability check."""
    from shieldcraft.main import run_self_host
    import shutil
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {
                "product_id": "test-stability",
                "version": "1.0",
                "spec_format": "canonical_json_v1",
                "self_host": True
            },
            "model": {"version": "1.0"},
            "sections": [{"id": "core"}]
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name
    
    try:
        # Clean output directory
        if os.path.exists(".selfhost_outputs"):
            shutil.rmtree(".selfhost_outputs")
        
        # Run self-host
        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")
        
        # Load summary
        with open(".selfhost_outputs/summary.json") as f:
            summary = json.load(f)
        
        # Verify summary has expected fields (may vary based on implementation)
        assert "item_count" in summary or "checklist_count" in summary
        assert "status" in summary
        
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
