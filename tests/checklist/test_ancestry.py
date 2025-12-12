"""
Test task ancestry tracking.
"""

from shieldcraft.services.checklist.ancestry import build_ancestry, verify_ancestry


def test_ancestry_basic_task():
    """Test ancestry for basic task."""
    items = [
        {
            "id": "task-1",
            "type": "task",
            "ptr": "/sections/0/task1",
            "lineage_id": "lineage-1",
            "classification": "task",
            "severity": "medium"
        }
    ]
    
    ancestry = build_ancestry(items)
    
    assert "task-1" in ancestry
    ancestry_data = ancestry["task-1"]
    
    # Should be a dict with chain and chain_hash
    assert isinstance(ancestry_data, dict)
    assert "chain" in ancestry_data
    assert "chain_hash" in ancestry_data
    
    chain = ancestry_data["chain"]
    
    # Should have progression
    assert "raw" in chain
    assert "extracted" in chain
    assert "normalized" in chain
    assert "final" in chain


def test_ancestry_derived_task():
    """Test ancestry for derived task."""
    items = [
        {
            "id": "fix-dep-1",
            "type": "fix-dependency",
            "ptr": "/dependencies/fix1",
            "lineage_id": "lineage-2",
            "classification": "fix-dependency",
            "severity": "high"
        }
    ]
    
    ancestry = build_ancestry(items)
    
    assert "fix-dep-1" in ancestry
    ancestry_data = ancestry["fix-dep-1"]
    
    # Should be a dict with chain
    assert isinstance(ancestry_data, dict)
    chain = ancestry_data["chain"]
    
    # Derived task should have derived stage
    assert "derived" in chain


def test_ancestry_verification():
    """Test ancestry verification."""
    ancestry = {
        "task-1": {"chain": ["raw", "extracted", "normalized", "final"], "chain_hash": "abc123"},
        "task-2": {"chain": ["raw", "extracted", "normalized", "final"], "chain_hash": "def456"}
    }
    
    result = verify_ancestry(ancestry)
    
    assert result["ok"] is True
    assert len(result["violations"]) == 0


def test_ancestry_gap_detection():
    """Test detection of gaps in ancestry."""
    ancestry = {
        "task-1": {"chain": ["raw", "final"], "chain_hash": "xyz789"}  # Missing intermediate stages
    }
    
    result = verify_ancestry(ancestry)
    
    # Should detect missing stages
    assert result["ok"] is False
    assert len(result["violations"]) > 0
