"""
Test resolution chain builder.
"""

from shieldcraft.services.checklist.resolution_chain import build_chain, verify_chains


def test_resolution_chain_basic():
    """Test basic resolution chain building."""
    items = [
        {
            "id": "task-1",
            "type": "task",
            "ptr": "/sections/0/task1"
        },
        {
            "id": "fix-dep-1",
            "type": "fix-dependency",
            "ptr": "/dependencies/fix1",
            "depends_on": ["/sections/0/task1"]
        }
    ]
    
    chains = build_chain(items)
    
    # Should have chain for derived task
    assert "fix-dep-1" in chains
    assert len(chains["fix-dep-1"]) > 0


def test_resolution_chain_verification():
    """Test chain verification."""
    chains = {
        "task-1": ["/a", "/b", "/c"],
        "task-2": ["/x", "/y"]
    }
    
    result = verify_chains(chains)
    
    assert result["ok"] is True
    assert len(result["violations"]) == 0


def test_resolution_chain_loop_detection():
    """Test loop detection in chains."""
    chains = {
        "task-1": ["/a", "/b", "/a"]  # Loop
    }
    
    result = verify_chains(chains)
    
    assert result["ok"] is False
    assert len(result["violations"]) > 0
    assert result["violations"][0]["issue"] == "chain_contains_loop"
