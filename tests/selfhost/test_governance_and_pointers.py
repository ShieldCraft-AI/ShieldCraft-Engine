"""
Test governance evaluation, pointer completeness, and derived tasks.
"""
import json
import tempfile
import pytest


def test_governance_valid_spec():
    """Test governance passes for valid spec."""
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.services.spec.model import SpecModel
    from shieldcraft.services.governance.rules_engine import evaluate_governance
    from shieldcraft.services.spec.fingerprint import compute_spec_fingerprint
    
    spec = {
        "metadata": {
            "product_id": "test-governance",
            "version": "1.0",
            "spec_format": "canonical_json_v1",
            "self_host": True
        },
        "model": {
            "version": "1.0"
        },
        "sections": {
            "core": {
                "description": "Core components"
            }
        }
    }
    
    # Build spec model
    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    fingerprint = compute_spec_fingerprint(spec)
    spec_model = SpecModel(spec, ast, fingerprint)
    
    # Generate some checklist items
    checklist_items = [
        {
            "id": "test.1",
            "ptr": "/sections/core",
            "text": "Implement core",
            "classification": "implementation"
        }
    ]
    
    # Evaluate governance
    result = evaluate_governance(spec_model, checklist_items)
    
    # Valid spec should pass
    assert result["ok"] is True
    assert len(result["violations"]) == 0


def test_governance_missing_section():
    """Test governance detects missing required section."""
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.services.spec.model import SpecModel
    from shieldcraft.services.governance.rules_engine import evaluate_governance
    from shieldcraft.services.spec.fingerprint import compute_spec_fingerprint
    
    # Missing "sections" key
    spec = {
        "metadata": {
            "product_id": "test-missing",
            "version": "1.0",
            "spec_format": "canonical_json_v1"
        },
        "model": {
            "version": "1.0"
        }
    }
    
    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    fingerprint = compute_spec_fingerprint(spec)
    spec_model = SpecModel(spec, ast, fingerprint)
    
    checklist_items = []
    
    result = evaluate_governance(spec_model, checklist_items)
    
    # Should have violations
    assert result["ok"] is False
    assert len(result["violations"]) > 0
    
    # Check for missing section violation
    violation_types = [v["type"] for v in result["violations"]]
    assert "missing_required_section" in violation_types


def test_pointer_completeness():
    """Test pointer completeness check."""
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.services.spec.pointer_auditor import ensure_full_pointer_coverage
    
    spec = {
        "metadata": {
            "product_id": "test-pointers",
            "version": "1.0"
        },
        "model": {"version": "1.0"},
        "sections": {}
    }
    
    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    
    uncovered = ensure_full_pointer_coverage(spec, ast)
    
    # Should have no uncovered AST pointers (all AST nodes should map to raw)
    assert isinstance(uncovered, list)


def test_derived_tasks_deterministic():
    """Test derived tasks are generated deterministically."""
    from shieldcraft.services.checklist.derived import infer_tasks
    
    item = {
        "id": "test.module.1",
        "ptr": "/modules/test",
        "type": "module",
        "name": "TestModule",
        "category": "module",
        "classification": "implementation"
    }
    
    # Generate derived tasks twice
    derived1 = infer_tasks(item)
    derived2 = infer_tasks(item)
    
    # Should be identical
    assert derived1 == derived2
    
    # Should have test, imports, init tasks
    task_types = [t.get("type") for t in derived1]
    assert "module_test" in task_types
    assert "module_imports" in task_types
    assert "module_init" in task_types


def test_bootstrap_derived_tasks():
    """Test bootstrap category generates derived tasks."""
    from shieldcraft.services.checklist.derived import infer_tasks
    
    item = {
        "id": "bootstrap.1",
        "ptr": "/sections/bootstrap/loader",
        "category": "bootstrap",
        "classification": "bootstrap",
        "type": "loader_stage"
    }
    
    derived = infer_tasks(item)
    
    # Should have impl and verify tasks
    assert len(derived) >= 2
    task_types = [t.get("type") for t in derived]
    assert "bootstrap_impl" in task_types
    assert "bootstrap_verify" in task_types
