"""
Test DSL authority lockdown.

Ensures no drift, no parallel DSLs, strict version enforcement.
"""
import json
import pytest
from pathlib import Path
from shieldcraft.services.spec.dsl_authority import verify_canonical_dsl, get_canonical_dsl_version


def test_missing_dsl_version():
    """Missing dsl_version must fail."""
    spec = {
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        }
    }
    
    with pytest.raises(ValueError, match="DSL authority violation.*expected dsl_version"):
        verify_canonical_dsl(spec)


def test_wrong_dsl_version():
    """Wrong dsl_version must fail."""
    spec = {
        "dsl_version": "legacy_v1",
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        }
    }
    
    with pytest.raises(ValueError, match="DSL authority violation.*canonical_v1_frozen"):
        verify_canonical_dsl(spec)


def test_alternate_schema_path():
    """Alternate schema path must fail."""
    spec = {
        "dsl_version": "canonical_v1_frozen",
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        }
    }
    
    with pytest.raises(ValueError, match="DSL authority violation.*schema path"):
        verify_canonical_dsl(spec, schema_path="alternate/schema.json")


def test_canonical_spec_passes():
    """Canonical spec with correct version must pass."""
    spec = {
        "dsl_version": "canonical_v1_frozen",
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        }
    }
    
    result = verify_canonical_dsl(spec)
    assert result is True


def test_canonical_spec_with_schema_path():
    """Canonical spec with canonical schema path must pass."""
    spec = {
        "dsl_version": "canonical_v1_frozen",
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        }
    }
    
    result = verify_canonical_dsl(spec, schema_path="spec/schemas/se_dsl_v1.schema.json")
    assert result is True


def test_get_canonical_version():
    """Test canonical version getter."""
    version = get_canonical_dsl_version()
    assert version == "canonical_v1_frozen"
