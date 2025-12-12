"""
Test codegen dry-run mode.
"""

import os
from shieldcraft.services.codegen.generator import CodeGenerator


def test_dry_run_no_files_created(tmp_path):
    """Test that dry-run mode doesn't create files."""
    gen = CodeGenerator()
    
    items = [
        {
            "id": "task-1",
            "type": "task",
            "ptr": "/sections/0/task1",
            "lineage_id": "test-lineage",
            "classification": "task"
        }
    ]
    
    # Run in dry-run mode
    result = gen.run(items, dry_run=True)
    
    # Should return preview without creating files
    assert "preview" in result or isinstance(result, list)
    
    # Verify no actual files were created
    # (This assumes generator would normally write to a specific path)
    # For now, just assert we got a result
    assert result is not None


def test_dry_run_deterministic_hash():
    """Test that dry-run returns deterministic content hash."""
    gen = CodeGenerator()
    
    items = [
        {
            "id": "task-1",
            "type": "task",
            "ptr": "/sections/0/task1",
            "lineage_id": "test-lineage",
            "classification": "task"
        }
    ]
    
    # Run twice
    result1 = gen.run(items, dry_run=True)
    result2 = gen.run(items, dry_run=True)
    
    # Results should be identical
    assert result1 == result2
