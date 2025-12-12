import pytest
from shieldcraft.services.codegen.generator import CodeGenerator
from shieldcraft.services.ast.builder import ASTBuilder


def test_codegen_generate_basic():
    gen = CodeGenerator()
    builder = ASTBuilder()
    
    spec = {"metadata": {}, "model": {}, "sections": {}}
    ast = builder.build(spec)
    
    items = [
        {"id": "ITEM-001", "ptr": "/test", "text": "Test item", "requires_code": True, "category": "default"}
    ]
    
    result = gen.generate(ast, items)
    
    assert "items" in result
    assert "count" in result
    assert result["count"] == 1


def test_codegen_template_matching():
    gen = CodeGenerator()
    
    # Test template mapping
    assert gen._get_template_name("api") == "api_handler.j2"
    assert gen._get_template_name("rule") == "rule.j2"
    assert gen._get_template_name("model") == "model.j2"
    assert gen._get_template_name("unknown") == "default.j2"


def test_codegen_no_code_required():
    gen = CodeGenerator()
    builder = ASTBuilder()
    
    spec = {"metadata": {}, "model": {}, "sections": {}}
    ast = builder.build(spec)
    
    items = [
        {"id": "ITEM-001", "ptr": "/test", "text": "Test item", "requires_code": False}
    ]
    
    result = gen.generate(ast, items)
    
    assert result["count"] == 0


def test_codegen_deterministic_output():
    gen = CodeGenerator()
    builder = ASTBuilder()
    
    spec = {"metadata": {}, "model": {}, "sections": {}}
    ast = builder.build(spec)
    
    items = [
        {"id": "ITEM-001", "ptr": "/test", "text": "Test", "requires_code": True, "category": "default"}
    ]
    
    result1 = gen.generate(ast, items)
    result2 = gen.generate(ast, items)
    
    # Should be deterministic
    assert result1 == result2
