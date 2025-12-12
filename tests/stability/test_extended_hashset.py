"""
Test extended hashset comparison for stability checks.
"""
import pytest


def test_compare_with_extended_hashes_identical():
    """Test that identical extended hashes pass comparison."""
    from shieldcraft.services.stability.stability import compare
    
    run1 = {
        "signature": "abc123",
        "evidence": {
            "items_hash": "hash1",
            "invariants_hash": "hash2",
            "dependency_graph_hash": "hash3"
        },
        "manifest": {}
    }
    
    run2 = {
        "signature": "abc123",
        "evidence": {
            "items_hash": "hash1",
            "invariants_hash": "hash2",
            "dependency_graph_hash": "hash3"
        },
        "manifest": {}
    }
    
    result = compare(run1, run2)
    
    assert result is True


def test_compare_with_extended_hashes_different_items():
    """Test that different items_hash fails comparison."""
    from shieldcraft.services.stability.stability import compare
    
    run1 = {
        "signature": "abc123",
        "evidence": {
            "items_hash": "hash1",
            "invariants_hash": "hash2",
            "dependency_graph_hash": "hash3"
        },
        "manifest": {}
    }
    
    run2 = {
        "signature": "abc123",
        "evidence": {
            "items_hash": "different_hash",
            "invariants_hash": "hash2",
            "dependency_graph_hash": "hash3"
        },
        "manifest": {}
    }
    
    result = compare(run1, run2)
    
    assert result is False


def test_compare_with_extended_hashes_different_invariants():
    """Test that different invariants_hash fails comparison."""
    from shieldcraft.services.stability.stability import compare
    
    run1 = {
        "signature": "abc123",
        "evidence": {
            "items_hash": "hash1",
            "invariants_hash": "hash2",
            "dependency_graph_hash": "hash3"
        },
        "manifest": {}
    }
    
    run2 = {
        "signature": "abc123",
        "evidence": {
            "items_hash": "hash1",
            "invariants_hash": "different_hash",
            "dependency_graph_hash": "hash3"
        },
        "manifest": {}
    }
    
    result = compare(run1, run2)
    
    assert result is False


def test_compare_with_extended_hashes_different_graph():
    """Test that different dependency_graph_hash fails comparison."""
    from shieldcraft.services.stability.stability import compare
    
    run1 = {
        "signature": "abc123",
        "evidence": {
            "items_hash": "hash1",
            "invariants_hash": "hash2",
            "dependency_graph_hash": "hash3"
        },
        "manifest": {}
    }
    
    run2 = {
        "signature": "abc123",
        "evidence": {
            "items_hash": "hash1",
            "invariants_hash": "hash2",
            "dependency_graph_hash": "different_hash"
        },
        "manifest": {}
    }
    
    result = compare(run1, run2)
    
    assert result is False


def test_compare_fallback_without_extended_hashes():
    """Test that comparison falls back to manifest when hashes not available."""
    from shieldcraft.services.stability.stability import compare
    
    run1 = {
        "signature": "abc123",
        "manifest": {"items": 10}
    }
    
    run2 = {
        "signature": "abc123",
        "manifest": {"items": 10}
    }
    
    result = compare(run1, run2)
    
    assert result is True
