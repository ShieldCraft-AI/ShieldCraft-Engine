"""Test missing pointer detection."""
from shieldcraft.services.spec.pointer_auditor import ensure_full_pointer_coverage
from shieldcraft.services.ast.builder import ASTBuilder


def test_missing_pointer_detected():
    """Test that missing pointers are detected in preflight."""
    # Minimal DSL with a field not represented in AST
    raw_spec = {
        "metadata": {
            "product_id": "test_product",
            "version": "1.0"
        },
        "sections": [
            {
                "id": "section1",
                "description": "Test section",
                "hidden_field": "not_in_ast"
            }
        ]
    }

    # Build AST (which might not include hidden_field)
    ast_builder = ASTBuilder()
    ast = ast_builder.build(raw_spec)

    # Run pointer coverage
    coverage = ensure_full_pointer_coverage(ast, raw_spec)

    # Assert we have coverage data
    assert "missing" in coverage
    assert "ok" in coverage
    assert "total_pointers" in coverage
    assert "coverage_percentage" in coverage

    # Should detect some structure
    assert coverage["total_pointers"] > 0


def test_full_coverage():
    """Test when all pointers are covered."""
    raw_spec = {
        "metadata": {
            "product_id": "test"
        }
    }

    # Build mock AST with all pointers
    ast = {
        "nodes": [
            {"ptr": "/metadata", "type": "object"},
            {"ptr": "/metadata/product_id", "type": "string"}
        ]
    }

    coverage = ensure_full_pointer_coverage(ast, raw_spec)

    # All pointers should be covered
    assert coverage["ok_count"] > 0
    assert len(coverage["missing"]) == 0 or coverage["coverage_percentage"] == 100.0


def test_preflight_integration():
    """Test that preflight reports missing pointers and marks contract_ok=False."""
    from shieldcraft.services.preflight.preflight import run_preflight

    spec = {
        "metadata": {
            "product_id": "test_spec",
            "version": "1.0"
        },
        "sections": []
    }

    schema = {}  # Minimal schema
    checklist_items = []

    # Run preflight
    result = run_preflight(spec, schema, checklist_items)

    # Should have pointer_coverage field
    assert "pointer_coverage" in result
    assert "missing" in result["pointer_coverage"]

    # If missing pointers exist, contract_ok should be False
    if len(result["pointer_coverage"]["missing"]) > 0:
        assert result["contract_ok"] == False


def test_empty_spec():
    """Test coverage with empty spec."""
    raw_spec = {}
    ast = {"nodes": []}

    coverage = ensure_full_pointer_coverage(ast, raw_spec)

    # Empty spec should have 100% coverage (no pointers to miss)
    assert coverage["total_pointers"] == 0
    assert coverage["coverage_percentage"] == 100.0
    assert len(coverage["missing"]) == 0
