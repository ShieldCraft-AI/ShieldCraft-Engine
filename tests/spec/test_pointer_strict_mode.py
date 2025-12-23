"""
Test pointer strict mode enforcement.
"""
from shieldcraft.services.ast.builder import ASTBuilder
from shieldcraft.services.spec.fingerprint import compute_spec_fingerprint
from shieldcraft.services.spec.model import SpecModel
from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_strict_mode_disabled_by_default():
    """Test that strict mode is disabled by default."""
    spec = {
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        },
        "sections": []
    }

    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    fingerprint = compute_spec_fingerprint(spec)

    # Default: strict_mode=False
    spec_model = SpecModel(spec, ast, fingerprint)
    assert spec_model.strict_mode == False


def test_strict_mode_enforces_full_coverage():
    """Test that strict mode requires all pointers to be covered."""
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
                    {
                        "id": "item1",
                        "text": "Item 1",
                        "severity": "high"
                    },
                    {
                        "id": "item2",
                        "text": "Item 2",
                        "severity": "medium"
                    }
                ]
            }
        ]
    }

    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    fingerprint = compute_spec_fingerprint(spec)

    # Enable strict mode
    spec_model = SpecModel(spec, ast, fingerprint, strict_mode=True)

    # Build checklist (should cover all items)
    generator = ChecklistGenerator()
    checklist_result = generator.build(spec)
    items = checklist_result["items"]

    # Validate coverage
    ok, missing = spec_model.validate_pointer_strict_mode(items)

    # Should pass (all pointers covered)
    assert ok, f"Strict mode validation failed with missing pointers: {missing}"
    assert len(missing) == 0


def test_strict_mode_detects_missing_pointers():
    """Test that strict mode detects uncovered pointers."""
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
                    {
                        "id": "item1",
                        "text": "Item 1",
                        "severity": "high"
                    }
                ]
            }
        ]
    }

    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    fingerprint = compute_spec_fingerprint(spec)

    # Enable strict mode
    spec_model = SpecModel(spec, ast, fingerprint, strict_mode=True)

    # Provide incomplete checklist (missing some pointers)
    incomplete_items = [
        {
            "id": "partial",
            "ptr": "/metadata",
            "text": "Partial coverage",
            "lineage_id": "test123"
        }
    ]

    # Validate coverage
    ok, missing = spec_model.validate_pointer_strict_mode(incomplete_items)

    # Should fail (missing pointers)
    assert not ok, "Strict mode should detect missing pointers"
    assert len(missing) > 0, "Should have missing pointers"


def test_strict_mode_allows_complete_coverage():
    """Test that strict mode passes with complete coverage."""
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

    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    fingerprint = compute_spec_fingerprint(spec)

    # Enable strict mode
    spec_model = SpecModel(spec, ast, fingerprint, strict_mode=True)

    # Build full checklist
    generator = ChecklistGenerator()
    checklist_result = generator.build(spec)
    items = checklist_result["items"]

    # Validate coverage
    ok, missing = spec_model.validate_pointer_strict_mode(items)

    # Should pass (complete coverage)
    assert ok, f"Strict mode should pass with complete coverage. Missing: {missing}"


def test_strict_mode_disabled_allows_partial_coverage():
    """Test that disabled strict mode allows partial coverage."""
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
            }
        ]
    }

    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    fingerprint = compute_spec_fingerprint(spec)

    # Strict mode disabled (default)
    spec_model = SpecModel(spec, ast, fingerprint, strict_mode=False)

    # Partial checklist
    partial_items = [
        {
            "id": "partial",
            "ptr": "/sections/0",
            "text": "Only one item",
            "lineage_id": "test123"
        }
    ]

    # Validate coverage
    ok, missing = spec_model.validate_pointer_strict_mode(partial_items)

    # Should pass (strict mode disabled)
    assert ok, "Disabled strict mode should allow partial coverage"
    assert len(missing) == 0
