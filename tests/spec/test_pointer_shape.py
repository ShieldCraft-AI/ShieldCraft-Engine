"""
Test pointer shape validation.
"""

from shieldcraft.services.spec.pointer_auditor import pointer_audit
from shieldcraft.services.ast.builder import ASTBuilder


def test_pointer_shape_double_slash():
    """Test detection of double slashes in pointer."""
    raw = {
        "sections": [{"id": "sec1"}]
    }
    
    ast = ASTBuilder().build(raw)
    
    items = [
        {
            "id": "task-1",
            "ptr": "/sections//0"  # Double slash
        }
    ]
    
    result = pointer_audit(raw, ast, items)
    
    # Should detect malformed pointer
    assert "pointer_shape_errors" in result


def test_pointer_shape_trailing_slash():
    """Test detection of trailing slash."""
    raw = {
        "sections": [{"id": "sec1"}]
    }
    
    ast = ASTBuilder().build(raw)
    
    items = [
        {
            "id": "task-1",
            "ptr": "/sections/0/"  # Trailing slash
        }
    ]
    
    result = pointer_audit(raw, ast, items)
    
    assert "pointer_shape_errors" in result


def test_pointer_shape_valid():
    """Test valid pointer passes."""
    raw = {
        "sections": [{"id": "sec1"}]
    }
    
    ast = ASTBuilder().build(raw)
    
    items = [
        {
            "id": "task-1",
            "ptr": "/sections/0"  # Valid
        }
    ]
    
    result = pointer_audit(raw, ast, items)
    
    # No shape errors for valid pointer
    if "pointer_shape_errors" in result:
        assert len(result["pointer_shape_errors"]) == 0
