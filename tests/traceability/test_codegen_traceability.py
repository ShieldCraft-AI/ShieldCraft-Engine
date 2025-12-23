from shieldcraft.services.codegen.generator import CodeGenerator
from shieldcraft.services.ast.builder import ASTBuilder


def test_codegen_traceability_metadata():
    """Test that codegen embeds traceability metadata."""
    gen = CodeGenerator()
    builder = ASTBuilder()

    spec = {"metadata": {}, "model": {}, "sections": {}}
    ast = builder.build(spec)

    items = [
        {
            "id": "ITEM-001",
            "ptr": "/test",
            "source_pointer": "/metadata/test",
            "source_section": "metadata",
            "text": "Test item",
            "requires_code": True,
            "category": "default"
        }
    ]

    result = gen.generate(ast, items)

    assert result["count"] == 1
    code_item = result["items"][0]

    # Check metadata is present
    assert "metadata" in code_item
    assert code_item["metadata"]["source_item_id"] == "ITEM-001"
    assert code_item["metadata"]["source_pointer"] == "/metadata/test"
    assert code_item["metadata"]["source_section"] == "metadata"


def test_codegen_traceability_in_code():
    """Test that traceability appears in generated code."""
    gen = CodeGenerator()
    builder = ASTBuilder()

    spec = {"metadata": {}, "model": {}, "sections": {}}
    ast = builder.build(spec)

    items = [
        {
            "id": "ITEM-002",
            "ptr": "/api/handler",
            "source_pointer": "/api/handler",
            "source_section": "api",
            "text": "API handler",
            "requires_code": True,
            "category": "default"
        }
    ]

    result = gen.generate(ast, items)
    code = result["items"][0]["code"]

    # Code should contain source pointer comment
    assert "/api/handler" in code


def test_codegen_bootstrap_routing():
    """Test that bootstrap category routes to bootstrap templates."""
    gen = CodeGenerator()

    item = {
        "category": "bootstrap",
        "type": "spec_loader"
    }

    template_name = gen._get_template_name("bootstrap", item)

    # Should route to bootstrap template or fallback
    assert "bootstrap" in template_name or template_name == "default.j2"


def test_codegen_traceability_deterministic():
    """Test that traceability metadata is deterministic."""
    gen = CodeGenerator()
    builder = ASTBuilder()

    spec = {"metadata": {}, "model": {}, "sections": {}}
    ast = builder.build(spec)

    items = [
        {
            "id": "ITEM-003",
            "ptr": "/test",
            "source_pointer": "/test",
            "source_section": "sections",
            "text": "Test",
            "requires_code": True,
            "category": "default"
        }
    ]

    result1 = gen.generate(ast, items)
    result2 = gen.generate(ast, items)

    # Metadata should be identical
    assert result1["items"][0]["metadata"] == result2["items"][0]["metadata"]


def test_codegen_no_traceability_when_not_required():
    """Test that items without requires_code don't generate code."""
    gen = CodeGenerator()
    builder = ASTBuilder()

    spec = {"metadata": {}, "model": {}, "sections": {}}
    ast = builder.build(spec)

    items = [
        {
            "id": "ITEM-004",
            "ptr": "/test",
            "source_pointer": "/test",
            "source_section": "test",
            "text": "No code needed",
            "requires_code": False,
            "category": "default"
        }
    ]

    result = gen.generate(ast, items)

    assert result["count"] == 0
