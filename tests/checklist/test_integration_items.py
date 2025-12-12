"""
Test integration task classification and codegen.
"""

from shieldcraft.services.checklist.classify import classify_item


def test_integration_classification():
    """Test that items referencing multiple sections are classified as integration."""
    item = {
        "id": "task-1",
        "type": "integration",
        "ptr": "/sections/0/tasks/0",
        "text": "Integrate components"
    }
    
    result = classify_item(item)
    assert result == "integration"


def test_integration_codegen_target():
    """Test that integration items map to integration target."""
    from shieldcraft.services.codegen.mapping_inspector import inspect
    
    items = [
        {
            "id": "task-1",
            "type": "integration",
            "ptr": "/integration/task1"
        }
    ]
    
    targets = inspect(items)
    
    assert len(targets) == 1
    assert targets[0]["target"] == "integration"
    assert targets[0]["item_id"] == "task-1"
