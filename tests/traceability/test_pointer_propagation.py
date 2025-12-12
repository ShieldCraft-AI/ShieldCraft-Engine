import pytest
from shieldcraft.services.checklist.extractor import SpecExtractor


def test_pointer_propagation_basic():
    """Test that pointers are propagated to extracted items."""
    extractor = SpecExtractor()
    
    spec = {
        "metadata": {"product_id": "test"},
        "sections": {"sec1": {"field1": "value1"}}
    }
    
    items = extractor.extract(spec)
    
    # All items should have source_pointer
    for item in items:
        assert "source_pointer" in item
        assert "source_section" in item
        assert "source_line" in item


def test_pointer_source_section():
    """Test that source_section is correctly determined."""
    extractor = SpecExtractor()
    
    spec = {
        "metadata": {"id": "test"},
        "model": {"version": "1.0"},
        "sections": {"sec1": {}}
    }
    
    items = extractor.extract(spec)
    
    # Find metadata items
    metadata_items = [i for i in items if i["source_section"] == "metadata"]
    assert len(metadata_items) > 0
    
    # Find model items
    model_items = [i for i in items if i["source_section"] == "model"]
    assert len(model_items) > 0


def test_pointer_deterministic_lines():
    """Test that source_line is deterministic."""
    extractor = SpecExtractor()
    
    spec = {
        "metadata": {"id": "test"},
        "sections": {}
    }
    
    items1 = extractor.extract(spec)
    items2 = extractor.extract(spec)
    
    # Line numbers should be deterministic
    for i1, i2 in zip(items1, items2):
        assert i1["source_line"] == i2["source_line"]


def test_pointer_traceability_nested():
    """Test pointer traceability for nested structures."""
    extractor = SpecExtractor()
    
    spec = {
        "sections": {
            "auth": {
                "fields": {
                    "enabled": True
                }
            }
        }
    }
    
    items = extractor.extract(spec)
    
    # Find the enabled field
    enabled_items = [i for i in items if "enabled" in i["ptr"]]
    assert len(enabled_items) > 0
    
    for item in enabled_items:
        assert item["source_pointer"] == item["ptr"]
        assert item["source_section"] == "sections"


def test_pointer_sorted_extraction():
    """Test that extraction is deterministic (sorted)."""
    extractor = SpecExtractor()
    
    spec = {
        "z_field": "last",
        "a_field": "first",
        "m_field": "middle"
    }
    
    items = extractor.extract(spec)
    
    # Extract just the top-level items
    top_level = [i for i in items if i["ptr"].count("/") == 1]
    keys = [i["key"] for i in top_level]
    
    # Should be sorted
    assert keys == sorted(keys)
