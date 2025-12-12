"""
Test lineage consistency across AST → Checklist → Codegen.
"""
import pytest
from shieldcraft.services.ast.builder import ASTBuilder
from shieldcraft.services.ast.lineage import build_lineage, get_lineage_map, verify_lineage_chain
from shieldcraft.services.checklist.generator import ChecklistGenerator
from shieldcraft.services.codegen.generator import CodeGenerator


def test_lineage_propagates_ast_to_checklist():
    """Test that lineage_id propagates from AST to checklist items."""
    spec = {
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        },
        "sections": [
            {
                "id": "sec1",
                "name": "Test Section",
                "items": [
                    {
                        "id": "item1",
                        "text": "Test item",
                        "severity": "high"
                    }
                ]
            }
        ]
    }
    
    # Build AST with lineage
    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    
    # Verify AST has lineage
    lineage_map = get_lineage_map(ast)
    assert len(lineage_map) > 0
    assert "/sections/0/items/0" in lineage_map
    
    # Build checklist
    generator = ChecklistGenerator()
    checklist_result = generator.build(spec)
    items = checklist_result["items"]
    
    # Verify all items have lineage_id
    for item in items:
        assert "lineage_id" in item, f"Item {item.get('id')} missing lineage_id"
        assert item["lineage_id"], f"Item {item.get('id')} has empty lineage_id"


def test_lineage_chain_integrity():
    """Test that lineage chain is intact (no duplicates, all unique)."""
    spec = {
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        },
        "sections": [
            {
                "id": "sec1",
                "name": "Section 1",
                "items": [
                    {"id": "item1", "text": "Item 1", "severity": "high"},
                    {"id": "item2", "text": "Item 2", "severity": "medium"}
                ]
            },
            {
                "id": "sec2",
                "name": "Section 2",
                "items": [
                    {"id": "item3", "text": "Item 3", "severity": "low"}
                ]
            }
        ]
    }
    
    # Build AST
    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    
    # Build lineage
    lineage_data = build_lineage(ast)
    
    # Verify lineage chain integrity
    ok, violations = verify_lineage_chain(lineage_data)
    
    assert ok, f"Lineage chain integrity failed: {violations}"
    assert len(violations) == 0


def test_derived_tasks_inherit_lineage():
    """Test that derived tasks inherit parent lineage_id."""
    spec = {
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        },
        "model": {
            "modules": [
                {
                    "name": "TestModule",
                    "type": "module",
                    "dependencies": []
                }
            ]
        },
        "sections": []
    }
    
    # Build checklist
    generator = ChecklistGenerator()
    checklist_result = generator.build(spec)
    items = checklist_result["items"]
    
    # Find module item
    module_items = [item for item in items if item.get("type") == "module"]
    assert len(module_items) > 0, "No module items found"
    
    module_item = module_items[0]
    assert "lineage_id" in module_item
    parent_lineage = module_item["lineage_id"]
    
    # Find derived tasks (test, imports, init)
    derived_items = [item for item in items if item.get("id", "").startswith(module_item["id"] + ".")]
    
    # All derived tasks should inherit parent's lineage_id
    for derived in derived_items:
        assert "lineage_id" in derived, f"Derived task {derived.get('id')} missing lineage_id"
        assert derived["lineage_id"] == parent_lineage, \
            f"Derived task {derived.get('id')} has different lineage_id: {derived['lineage_id']} != {parent_lineage}"


def test_lineage_deterministic_across_builds():
    """Test that lineage_id is deterministic across multiple builds."""
    spec = {
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        },
        "sections": [
            {
                "id": "sec1",
                "name": "Test Section",
                "items": [
                    {"id": "item1", "text": "Test item", "severity": "high"}
                ]
            }
        ]
    }
    
    # Build AST twice
    ast_builder1 = ASTBuilder()
    ast1 = ast_builder1.build(spec)
    
    ast_builder2 = ASTBuilder()
    ast2 = ast_builder2.build(spec)
    
    # Get lineage maps
    lineage_map1 = get_lineage_map(ast1)
    lineage_map2 = get_lineage_map(ast2)
    
    # Should be identical
    assert lineage_map1 == lineage_map2, "Lineage is not deterministic"


def test_codegen_injects_lineage_headers():
    """Test that generated code includes lineage headers."""
    spec = {
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        },
        "model": {
            "modules": [
                {
                    "name": "TestModule",
                    "type": "module",
                    "dependencies": []
                }
            ]
        },
        "sections": []
    }
    
    # Build checklist
    generator = ChecklistGenerator()
    checklist_result = generator.build(spec)
    items = checklist_result["items"]
    
    # Run codegen
    codegen = CodeGenerator()
    outputs = codegen.run({"items": items})
    
    # Check that at least one output has lineage header
    found_lineage_header = False
    for output in outputs:
        content = output.get("content", "")
        if "Lineage ID:" in content and "Source Pointer:" in content:
            found_lineage_header = True
            break
    
    assert found_lineage_header, "No lineage headers found in generated code"
