import pytest
from shieldcraft.services.plan.execution_plan import from_ast
from shieldcraft.services.ast.builder import ASTBuilder


def test_from_ast_seven_phases():
    builder = ASTBuilder()
    spec = {
        "metadata": {"id": "test"},
        "model": {},
        "sections": {}
    }
    ast = builder.build(spec)
    
    plan = from_ast(ast)
    
    assert "phases" in plan
    assert len(plan["phases"]) == 8  # Updated to include cycle_resolution
    assert plan["phases"] == [
        "dsl_validation",
        "ast_construction",
        "schema_contracts",
        "checklist_generation",
        "cycle_resolution",
        "codegen",
        "artifact_bundling",
        "stability_verification"
    ]


def test_from_ast_deterministic_steps():
    builder = ASTBuilder()
    spec = {
        "metadata": {"id": "test"},
        "model": {},
        "sections": {}
    }
    ast = builder.build(spec)
    
    plan1 = from_ast(ast)
    plan2 = from_ast(ast)
    
    # Should be deterministic
    assert plan1["steps"] == plan2["steps"]
    assert plan1["ast_hash"] == plan2["ast_hash"]


def test_from_ast_step_structure():
    builder = ASTBuilder()
    spec = {"metadata": {}, "model": {}, "sections": {}}
    ast = builder.build(spec)
    
    plan = from_ast(ast)
    
    assert "steps" in plan
    assert len(plan["steps"]) == 8  # Updated to include cycle_resolution
    
    for step in plan["steps"]:
        assert "id" in step
        assert "phase" in step
        assert "order" in step
        assert "status" in step
        assert step["status"] == "pending"


def test_from_ast_stable_ordering():
    builder = ASTBuilder()
    spec = {
        "z_field": "last",
        "a_field": "first",
        "metadata": {},
        "model": {},
        "sections": {}
    }
    ast = builder.build(spec)
    
    plan = from_ast(ast)
    
    # Phases should be in fixed order
    for idx, step in enumerate(plan["steps"]):
        assert step["order"] == idx
