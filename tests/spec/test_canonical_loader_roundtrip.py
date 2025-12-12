"""
Test canonical loader roundtrip:
- Load spec
- Validate SpecModel returned
- Verify fingerprint computed
- Verify AST non-empty
- Verify pointer_index() works
"""
import json
import pytest
from pathlib import Path
from shieldcraft.dsl.canonical_loader import load_canonical_spec


def test_canonical_loader_roundtrip_minimal():
    """Test canonical loader with minimal inline fixture."""
    # Create minimal canonical spec
    minimal_spec = {
        "metadata": {
            "generator_version": "1.0.0",
            "canonical_spec_hash": "placeholder",
            "float_precision": 2
        },
        "sections": [
            {
                "id": "test_section",
                "tasks": [
                    {
                        "id": "task_1",
                        "description": "Test task"
                    }
                ]
            }
        ]
    }
    
    # Write to temp file
    temp_file = Path("/tmp/test_canonical_spec.json")
    temp_file.write_text(json.dumps(minimal_spec, sort_keys=True))
    
    # Load using canonical loader
    spec_model = load_canonical_spec(str(temp_file))
    
    # Assert SpecModel properties
    assert spec_model is not None
    assert spec_model.raw is not None
    assert spec_model.ast is not None
    assert spec_model.fingerprint is not None
    assert len(spec_model.fingerprint) == 64  # SHA256 hex
    
    # Verify AST non-empty
    assert hasattr(spec_model.ast, 'walk')
    nodes = list(spec_model.ast.walk())
    assert len(nodes) > 0
    
    # Verify pointer_index() non-empty
    pointer_index = spec_model.pointer_index()
    assert pointer_index is not None
    assert len(pointer_index) > 0
    
    # Verify get_sections() works
    sections = spec_model.get_sections()
    assert len(sections) >= 1
    
    # Cleanup
    temp_file.unlink()


def test_canonical_loader_with_template_spec():
    """Test canonical loader with template spec if it exists."""
    template_path = Path(__file__).parent.parent.parent / "spec" / "se_dsl_v1.spec.json"
    
    if not template_path.exists():
        pytest.skip("Template spec not found")
    
    # Load template spec
    spec_model = load_canonical_spec(str(template_path))
    
    # Verify loaded successfully
    assert spec_model is not None
    assert spec_model.fingerprint is not None
    assert spec_model.ast is not None
    
    # Verify pointer index
    pointer_index = spec_model.pointer_index()
    assert len(pointer_index) > 0


def test_canonical_loader_sorts_keys():
    """Test that loader canonicalizes unsorted keys."""
    unsorted_spec = {
        "sections": [],
        "metadata": {"generator_version": "1.0.0"},
        "canonical": True
    }
    
    temp_file = Path("/tmp/test_unsorted_spec.json")
    # Write with unsorted keys
    temp_file.write_text(json.dumps(unsorted_spec, sort_keys=False))
    
    spec_model = load_canonical_spec(str(temp_file))
    
    # Verify canonicalized (keys sorted)
    raw_keys = list(spec_model.raw.keys())
    assert raw_keys == sorted(raw_keys)
    
    temp_file.unlink()


def test_canonical_loader_float_precision():
    """Test float precision handling."""
    spec_with_floats = {
        "metadata": {
            "generator_version": "1.0.0",
            "float_precision": 3
        },
        "sections": [],
        "test_value": 3.14159265359
    }
    
    temp_file = Path("/tmp/test_float_spec.json")
    temp_file.write_text(json.dumps(spec_with_floats))
    
    spec_model = load_canonical_spec(str(temp_file))
    
    # Verify float rounded to precision
    assert spec_model.raw["test_value"] == 3.142
    
    temp_file.unlink()
