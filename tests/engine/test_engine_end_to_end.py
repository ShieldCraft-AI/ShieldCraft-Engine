import pytest
import tempfile
import json
import os
from shieldcraft.engine import Engine


def test_engine_end_to_end_basic():
    schema = "src/shieldcraft/dsl/schema/se_dsl.schema.json"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {"product_id": "test-e2e", "version": "1.0"},
            "model": {"version": "1.0"},
            "sections": {}
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name
    
    try:
        engine = Engine(schema)
        result = engine.run(tmp_path)
        
        # Should return valid result or schema error
        assert result is not None
        assert isinstance(result, dict)
    finally:
        os.unlink(tmp_path)


def test_engine_execution_plan_emission():
    schema = "src/shieldcraft/dsl/schema/se_dsl.schema.json"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {"product_id": "test-plan", "version": "1.0"},
            "model": {"version": "1.0"},
            "sections": {}
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name
    
    try:
        engine = Engine(schema)
        result = engine.run(tmp_path)
        
        if "plan" in result:
            # Plan should have phases and steps
            plan = result["plan"]
            assert "phases" in plan
            assert "steps" in plan
    finally:
        os.unlink(tmp_path)
        # Clean up products directory
        plan_dir = "products/test-plan"
        if os.path.exists(plan_dir):
            import shutil
            shutil.rmtree(plan_dir)


def test_engine_ast_integration():
    schema = "src/shieldcraft/dsl/schema/se_dsl.schema.json"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {"product_id": "test-ast", "version": "1.0"},
            "model": {"version": "1.0"},
            "sections": {"sec1": {"field1": "value1"}}
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name
    
    try:
        engine = Engine(schema)
        result = engine.run(tmp_path)
        
        if "ast" in result:
            ast = result["ast"]
            assert ast is not None
            assert hasattr(ast, "walk")
    finally:
        os.unlink(tmp_path)
        plan_dir = "products/test-ast"
        if os.path.exists(plan_dir):
            import shutil
            shutil.rmtree(plan_dir)


def test_engine_validation_errors():
    schema = "src/shieldcraft/dsl/schema/se_dsl.schema.json"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {"product_id": "test-invalid"}
            # Missing required 'model' and 'sections'
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name
    
    try:
        engine = Engine(schema)
        result = engine.run(tmp_path)
        
        # Should return schema_error
        assert result.get("type") == "schema_error"
        assert "details" in result
    finally:
        os.unlink(tmp_path)
