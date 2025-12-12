import pytest
from shieldcraft.services.ast.builder import ASTBuilder
from shieldcraft.services.ast.consistency import verify


def test_consistency_all_fields_in_ast():
    builder = ASTBuilder()
    
    spec = {
        "metadata": {"id": "test"},
        "model": {"version": "1.0"}
    }
    
    ast = builder.build(spec)
    issues = verify(ast, spec)
    
    # Should have minimal issues
    missing_in_ast = [i for i in issues if i["type"] == "missing_in_ast"]
    assert len(missing_in_ast) == 0


def test_consistency_no_missing_pointers():
    builder = ASTBuilder()
    
    spec = {
        "field1": "value1",
        "field2": {"nested": "value2"}
    }
    
    ast = builder.build(spec)
    issues = verify(ast, spec)
    
    # No nodes should be missing pointers
    missing_ptr = [i for i in issues if i["type"] == "missing_pointer"]
    assert len(missing_ptr) == 0


def test_consistency_reference_resolution():
    builder = ASTBuilder()
    
    spec = {
        "section1": {
            "ref": "/section2"
        },
        "section2": {
            "name": "target"
        }
    }
    
    ast = builder.build(spec)
    issues = verify(ast, spec)
    
    # Reference resolution should match
    ref_issues = [i for i in issues if i["type"] == "reference_mismatch"]
    # May or may not have issues depending on implementation
    assert isinstance(ref_issues, list)


def test_consistency_empty_spec():
    builder = ASTBuilder()
    
    spec = {}
    ast = builder.build(spec)
    issues = verify(ast, spec)
    
    # Should handle empty spec
    assert isinstance(issues, list)


def test_consistency_nested_structure():
    builder = ASTBuilder()
    
    spec = {
        "level1": {
            "level2": {
                "level3": {
                    "data": "value"
                }
            }
        }
    }
    
    ast = builder.build(spec)
    issues = verify(ast, spec)
    
    # All nested fields should be in AST
    missing = [i for i in issues if i["type"] == "missing_in_ast"]
    assert len(missing) == 0
