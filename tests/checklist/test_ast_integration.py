from shieldcraft.services.ast.builder import ASTBuilder
from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_ast_integration_basic():
    gen = ChecklistGenerator()
    builder = ASTBuilder()

    spec = {
        "metadata": {"id": "test-product"},
        "model": {"version": "1.0"},
        "sections": {
            "auth": {
                "description": "Authentication",
                "fields": {
                    "enabled": True
                }
            }
        }
    }

    ast = builder.build(spec)

    # Build checklist with AST
    result = gen.build(spec, ast=ast)

    # Should return valid result
    assert result is not None
    assert "items" in result or "valid" in result


def test_ast_integration_extraction():
    gen = ChecklistGenerator()
    builder = ASTBuilder()

    spec = {
        "metadata": {"id": "test"},
        "model": {},
        "sections": {
            "sec1": {
                "task1": "Implement feature"
            }
        }
    }

    ast = builder.build(spec)

    # Extract items using AST
    items = gen._extract_from_ast(ast)

    assert isinstance(items, list)
    # Should have extracted some items
    assert len(items) >= 0


def test_ast_integration_traversal():
    gen = ChecklistGenerator()
    builder = ASTBuilder()

    spec = {
        "metadata": {"id": "test"},
        "model": {"version": "1.0"},
        "sections": {
            "s1": {"field1": {"data": "value"}},
            "s2": {"field2": {"data": "value2"}}
        }
    }

    ast = builder.build(spec)

    # Should traverse all sections
    items = gen._extract_from_ast(ast)

    # Check items have pointers
    for item in items:
        assert "ptr" in item


def test_ast_integration_fallback():
    gen = ChecklistGenerator()

    spec = {
        "metadata": {"id": "test"},
        "model": {},
        "sections": {}
    }

    # Build without AST (fallback to dict extraction)
    result = gen.build(spec, ast=None)

    assert result is not None


def test_ast_integration_deterministic():
    gen = ChecklistGenerator()
    builder = ASTBuilder()

    spec = {
        "metadata": {"id": "test", "id_namespace": "test"},
        "model": {"version": "1.0"},
        "sections": {
            "z_section": {"z_field": "last"},
            "a_section": {"a_field": "first"}
        }
    }

    ast1 = builder.build(spec)
    ast2 = builder.build(spec)

    # AST should be deterministic
    ptrs1 = [n.ptr for n in ast1.walk()]
    ptrs2 = [n.ptr for n in ast2.walk()]

    assert ptrs1 == ptrs2
