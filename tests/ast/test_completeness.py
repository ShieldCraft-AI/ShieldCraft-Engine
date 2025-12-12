"""
Test AST completeness.
Ensure every raw field appears in AST (1:1 coverage).
"""
import json
import tempfile
import pytest


def test_raw_to_ast_completeness():
    """Test that all raw spec fields appear in AST."""
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.services.spec.pointer_auditor import extract_json_pointers, check_unreachable_pointers
    
    # Create minimal spec
    spec = {
        "metadata": {
            "product_id": "test-completeness",
            "version": "1.0"
        },
        "model": {
            "version": "1.0"
        },
        "sections": {
            "core": {
                "description": "Core section"
            }
        }
    }
    
    # Build AST
    builder = ASTBuilder()
    ast = builder.build(spec)
    
    # Check for unreachable pointers
    unreachable = check_unreachable_pointers(ast, spec)
    
    # All pointers should be reachable in AST
    assert len(unreachable) == 0, f"Unreachable pointers found: {unreachable}"


def test_ast_coverage_nested_structures():
    """Test AST coverage for nested structures."""
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.services.spec.pointer_auditor import check_unreachable_pointers
    
    spec = {
        "metadata": {
            "product_id": "test-nested",
            "version": "1.0"
        },
        "model": {"version": "1.0"},
        "sections": {
            "api": {
                "endpoints": [
                    {
                        "path": "/health",
                        "method": "GET"
                    },
                    {
                        "path": "/status",
                        "method": "GET"
                    }
                ]
            }
        }
    }
    
    builder = ASTBuilder()
    ast = builder.build(spec)
    
    unreachable = check_unreachable_pointers(ast, spec)
    
    # Should have full coverage
    assert len(unreachable) == 0


def test_ast_coverage_with_arrays():
    """Test AST coverage handles arrays correctly."""
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.services.spec.pointer_auditor import check_unreachable_pointers
    
    spec = {
        "metadata": {
            "product_id": "test-arrays",
            "version": "1.0"
        },
        "model": {"version": "1.0"},
        "sections": {
            "config": {
                "items": ["item1", "item2", "item3"]
            }
        }
    }
    
    builder = ASTBuilder()
    ast = builder.build(spec)
    
    unreachable = check_unreachable_pointers(ast, spec)
    
    # All array elements should be in AST
    assert len(unreachable) == 0
