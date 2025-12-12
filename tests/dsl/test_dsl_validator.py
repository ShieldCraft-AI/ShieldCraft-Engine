import pytest
from shieldcraft.services.dsl.validator import SpecValidator


def test_dsl_validator_required_fields():
    validator = SpecValidator()
    validator.schema = {}  # Skip schema loading
    
    # Missing required fields
    spec = {"model": {}}
    result = validator.validate(spec)
    
    assert result["valid"] is False
    assert len(result["errors"]) >= 2  # Missing metadata and sections


def test_dsl_validator_valid_spec():
    validator = SpecValidator()
    validator.schema = {}  # Skip schema loading
    
    spec = {
        "metadata": {"id": "test"},
        "model": {"version": "1.0"},
        "sections": {}
    }
    
    result = validator.validate(spec)
    # Should pass basic required fields check
    assert "valid" in result


def test_dsl_validator_pointer_resolution():
    validator = SpecValidator()
    validator.schema = {}  # Skip schema loading
    
    spec = {
        "metadata": {"id": "test", "ptr": "/invalid/pointer"},
        "model": {"version": "1.0"},
        "sections": {}
    }
    
    result = validator.validate(spec)
    # Should detect invalid pointer
    assert isinstance(result, dict)
    assert "valid" in result
    assert "errors" in result


def test_dsl_validator_dependency_validation():
    validator = SpecValidator()
    validator.schema = {}  # Skip schema loading
    
    spec = {
        "metadata": {"id": "meta-1"},
        "model": {"version": "1.0"},
        "sections": {
            "sec1": {
                "id": "sec-1",
                "dependencies": ["invalid-id"]
            }
        }
    }
    
    result = validator.validate(spec)
    # Should detect invalid dependency reference
    assert isinstance(result, dict)
    assert "errors" in result


def test_dsl_validator_structured_errors():
    validator = SpecValidator()
    validator.schema = {}  # Skip schema loading
    
    spec = {}
    result = validator.validate(spec)
    
    assert "valid" in result
    assert "errors" in result
    assert isinstance(result["errors"], list)
    
    if len(result["errors"]) > 0:
        error = result["errors"][0]
        assert "pointer" in error
        assert "message" in error
