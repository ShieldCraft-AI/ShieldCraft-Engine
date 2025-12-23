"""
Test ID collision detection.
"""

from shieldcraft.services.checklist.id_registry import IDRegistry, create_registry


def test_id_registry_basic():
    """Test basic ID registration."""
    registry = IDRegistry()

    assert registry.register("task-1") is True
    assert registry.register("task-2") is True
    assert registry.has_duplicates() is False


def test_id_registry_duplicate_detection():
    """Test duplicate ID detection."""
    registry = IDRegistry()

    registry.register("task-1", {"id": "task-1", "type": "task"})
    is_unique = registry.register("task-1", {"id": "task-1", "type": "module"})

    assert is_unique is False
    assert registry.has_duplicates() is True

    duplicates = registry.get_duplicates()
    assert len(duplicates) == 1
    assert duplicates[0]["id"] == "task-1"


def test_create_registry_from_items():
    """Test creating registry from items list."""
    items = [
        {"id": "task-1", "type": "task"},
        {"id": "task-2", "type": "task"},
        {"id": "task-1", "type": "module"}  # Duplicate
    ]

    registry = create_registry(items)

    assert registry.has_duplicates() is True
    assert len(registry.get_duplicates()) == 1


def test_get_all_ids_sorted():
    """Test getting all IDs in sorted order."""
    registry = IDRegistry()

    registry.register("task-3")
    registry.register("task-1")
    registry.register("task-2")

    all_ids = registry.get_all_ids()

    assert all_ids == ["task-1", "task-2", "task-3"]
