"""
Test classification type dimension.
"""
import pytest


def test_classify_type_structural():
    """Test that meta items are classified as structural."""
    from shieldcraft.services.checklist.classify import classify_type
    
    item = {"id": "meta::version", "category": "core", "origin": {}}
    
    result = classify_type(item)
    
    assert result == "structural"


def test_classify_type_governance():
    """Test that invariant category items are classified as governance."""
    from shieldcraft.services.checklist.classify import classify_type
    
    item = {"id": "item1", "category": "invariant", "origin": {}}
    
    result = classify_type(item)
    
    assert result == "governance"


def test_classify_type_bootstrap():
    """Test that bootstrap category items are classified as bootstrap."""
    from shieldcraft.services.checklist.classify import classify_type
    
    item = {"id": "item1", "category": "bootstrap", "origin": {}}
    
    result = classify_type(item)
    
    assert result == "bootstrap"


def test_classify_type_behavioral():
    """Test that derived items are classified as behavioral."""
    from shieldcraft.services.checklist.classify import classify_type
    
    item = {"id": "item1", "category": "core", "origin": {"source": "derived"}}
    
    result = classify_type(item)
    
    assert result == "behavioral"


def test_classify_type_default():
    """Test that default classification is structural."""
    from shieldcraft.services.checklist.classify import classify_type
    
    item = {"id": "item1", "category": "core", "origin": {}}
    
    result = classify_type(item)
    
    assert result == "structural"
