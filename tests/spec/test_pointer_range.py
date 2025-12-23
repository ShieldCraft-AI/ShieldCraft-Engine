"""
Test pointer range validation in pointer_auditor.
"""

from shieldcraft.services.spec.pointer_auditor import pointer_audit
from shieldcraft.services.ast.builder import ASTBuilder


def test_pointer_range_error_missing_array():
    """Test pointer range error when base pointer doesn't exist."""
    raw = {
        "sections": [
            {
                "id": "section1",
                "tasks": []
            }
        ]
    }

    # Create minimal AST
    ast = ASTBuilder().build(raw)

    # Create checklist item with wildcard reference to non-existent array
    items = [
        {
            "id": "task-1",
            "ptr": "/sections/0/missing_array[*]"
        }
    ]

    result = pointer_audit(raw, ast, items)

    # Should have pointer range error
    assert len(result["pointer_range_errors"]) == 1
    error = result["pointer_range_errors"][0]
    assert error["error"] == "base_pointer_not_found"
    assert error["base_pointer"] == "/sections/0/missing_array"


def test_pointer_range_error_not_array():
    """Test pointer range error when base pointer is not an array."""
    raw = {
        "sections": [
            {
                "id": "section1",
                "name": "Test Section"  # Not an array
            }
        ]
    }

    ast = ASTBuilder().build(raw)

    # Create item referencing string field with wildcard
    items = [
        {
            "id": "task-1",
            "ptr": "/sections/0/name[*]"
        }
    ]

    result = pointer_audit(raw, ast, items)

    # Should have error
    assert len(result["pointer_range_errors"]) == 1
    error = result["pointer_range_errors"][0]
    assert error["error"] == "not_an_array"


def test_pointer_range_error_empty_array():
    """Test pointer range error when array is empty."""
    raw = {
        "sections": [
            {
                "id": "section1",
                "tasks": []  # Empty array
            }
        ]
    }

    ast = ASTBuilder().build(raw)

    # Create item referencing empty array with wildcard
    items = [
        {
            "id": "task-1",
            "ptr": "/sections/0/tasks[*]"
        }
    ]

    result = pointer_audit(raw, ast, items)

    # Should have error
    assert len(result["pointer_range_errors"]) == 1
    error = result["pointer_range_errors"][0]
    assert error["error"] == "empty_array"


def test_pointer_range_valid():
    """Test no errors when array exists and has elements."""
    raw = {
        "sections": [
            {
                "id": "section1",
                "tasks": [
                    {"id": "task1", "name": "Task 1"},
                    {"id": "task2", "name": "Task 2"}
                ]
            }
        ]
    }

    ast = ASTBuilder().build(raw)

    # Create item referencing valid array with wildcard
    items = [
        {
            "id": "task-1",
            "ptr": "/sections/0/tasks[*]"
        }
    ]

    result = pointer_audit(raw, ast, items)

    # Should have no errors
    assert len(result["pointer_range_errors"]) == 0


def test_pointer_range_wildcard_slash():
    """Test pointer range with /* notation."""
    raw = {
        "config": {
            "items": [1, 2, 3]
        }
    }

    ast = ASTBuilder().build(raw)

    # Use /* notation
    items = [
        {
            "id": "task-1",
            "ptr": "/config/items/*"
        }
    ]

    result = pointer_audit(raw, ast, items)

    # Should have no errors (valid array)
    assert len(result["pointer_range_errors"]) == 0
