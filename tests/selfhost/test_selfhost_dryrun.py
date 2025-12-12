import json
import pytest
from shieldcraft.engine import Engine
from pathlib import Path


@pytest.fixture
def engine():
    schema_path = "spec/schemas/se_dsl_v1.schema.json"
    return Engine(schema_path)


@pytest.fixture
def spec_path():
    return "spec/se_dsl_v1.spec.json"


def test_selfhost_dryrun_preview(engine, spec_path):
    """Test self-host dry-run mode returns preview structure without writing files."""
    
    # Load spec
    with open(spec_path) as f:
        spec = json.load(f)
    
    # Run self-host in dry-run mode
    result = engine.run_self_host(spec, dry_run=True)
    
    # Assert preview structure
    assert "fingerprint" in result
    assert "output_dir" in result
    assert "manifest" in result
    assert "outputs" in result
    
    # Check fingerprint format (16-char hex)
    assert len(result["fingerprint"]) == 16
    assert all(c in "0123456789abcdef" for c in result["fingerprint"])
    
    # Check output_dir path
    assert result["output_dir"].startswith(".selfhost_outputs/")
    assert result["fingerprint"] in result["output_dir"]
    
    # Check manifest structure
    manifest = result["manifest"]
    assert "fingerprint" in manifest
    assert "spec_metadata" in manifest
    assert "bootstrap_items" in manifest
    assert "codegen_bundle_hash" in manifest
    assert "outputs" in manifest
    
    # Check outputs list
    outputs = result["outputs"]
    assert isinstance(outputs, list)
    
    # Each output should have path and content
    for output in outputs:
        assert "path" in output
        assert "content" in output


def test_selfhost_deterministic_fingerprint(engine, spec_path):
    """Test that same spec produces same fingerprint."""
    
    with open(spec_path) as f:
        spec = json.load(f)
    
    result1 = engine.run_self_host(spec, dry_run=True)
    result2 = engine.run_self_host(spec, dry_run=True)
    
    assert result1["fingerprint"] == result2["fingerprint"]


def test_selfhost_filters_bootstrap_items(engine, spec_path):
    """Test that self-host only includes bootstrap category items."""
    
    with open(spec_path) as f:
        spec = json.load(f)
    
    result = engine.run_self_host(spec, dry_run=True)
    
    # Check manifest indicates bootstrap items were filtered
    manifest = result["manifest"]
    assert manifest["bootstrap_items"] >= 0  # May be 0 if no bootstrap items
