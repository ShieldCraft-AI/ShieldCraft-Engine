"""
Test pointer locality warnings.
"""
import pytest
from shieldcraft.services.ast.builder import ASTBuilder
from shieldcraft.services.spec.pointer_auditor import pointer_audit


def test_pointer_locality_warning_cross_section():
    """Test that pointers reaching across unrelated sections generate warnings."""
    spec = {
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        },
        "sections": [
            {
                "id": "section_a",
                "name": "Section A",
                "items": [
                    {
                        "id": "item_a1",
                        "text": "Item A1",
                        "severity": "high"
                    }
                ]
            },
            {
                "id": "section_b",
                "name": "Section B",
                "items": [
                    {
                        "id": "item_b1",
                        "text": "Item B1",
                        "severity": "medium",
                        "depends_on": ["/sections/0/items/0"]  # Cross-section reference
                    }
                ]
            }
        ]
    }
    
    # Build AST
    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    
    # Create checklist items with cross-section reference
    checklist_items = [
        {
            "id": "item_a1",
            "ptr": "/sections/0/items/0",
            "text": "Item A1"
        },
        {
            "id": "item_b1",
            "ptr": "/sections/1/items/0",
            "text": "Item B1",
            "depends_on": ["/sections/0/items/0"]  # Reference to different section
        }
    ]
    
    # Run audit
    audit_result = pointer_audit(spec, ast, checklist_items)
    
    # Check for locality warnings
    locality_warnings = audit_result.get("locality_warnings", [])
    
    assert len(locality_warnings) > 0, "Should detect cross-section pointer reference"
    
    # Verify warning details
    warning = locality_warnings[0]
    assert warning["item_section"] != warning["reference_section"], \
        "Warning should indicate different sections"


def test_pointer_locality_no_warning_same_section():
    """Test that pointers within same section don't generate warnings."""
    spec = {
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        },
        "sections": [
            {
                "id": "section_a",
                "name": "Section A",
                "items": [
                    {
                        "id": "item_a1",
                        "text": "Item A1",
                        "severity": "high"
                    },
                    {
                        "id": "item_a2",
                        "text": "Item A2",
                        "severity": "medium",
                        "depends_on": ["/sections/0/items/0"]  # Same section reference
                    }
                ]
            }
        ]
    }
    
    # Build AST
    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    
    # Create checklist items with same-section reference
    checklist_items = [
        {
            "id": "item_a1",
            "ptr": "/sections/0/items/0",
            "text": "Item A1"
        },
        {
            "id": "item_a2",
            "ptr": "/sections/0/items/1",
            "text": "Item A2",
            "depends_on": ["/sections/0/items/0"]  # Same section
        }
    ]
    
    # Run audit
    audit_result = pointer_audit(spec, ast, checklist_items)
    
    # Check for locality warnings
    locality_warnings = audit_result.get("locality_warnings", [])
    
    # Should have no warnings for same-section references
    assert len(locality_warnings) == 0, "Should not warn for same-section references"


def test_pointer_locality_multiple_violations():
    """Test detection of multiple cross-section violations."""
    spec = {
        "metadata": {
            "product_id": "test",
            "version": "1.0"
        },
        "sections": [
            {
                "id": "section_a",
                "name": "Section A"
            },
            {
                "id": "section_b",
                "name": "Section B"
            },
            {
                "id": "section_c",
                "name": "Section C"
            }
        ]
    }
    
    # Build AST
    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    
    # Create items with multiple cross-section references
    checklist_items = [
        {
            "id": "item_b",
            "ptr": "/sections/1",
            "text": "Item B",
            "depends_on": ["/sections/0", "/sections/2"]  # Multiple cross-refs
        }
    ]
    
    # Run audit
    audit_result = pointer_audit(spec, ast, checklist_items)
    
    # Should detect both violations
    locality_warnings = audit_result.get("locality_warnings", [])
    assert len(locality_warnings) >= 2, "Should detect multiple cross-section references"
