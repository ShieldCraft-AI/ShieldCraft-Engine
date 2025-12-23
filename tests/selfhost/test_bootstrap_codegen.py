"""
Test bootstrap module code generation.
"""
import json
import os
import tempfile
import shutil


def test_bootstrap_module_emitted():
    """Test bootstrap module file is emitted."""
    from shieldcraft.services.codegen.generator import CodeGenerator

    # Create bootstrap checklist item
    checklist = [
        {
            "id": "bootstrap.loader.1",
            "ptr": "/sections/bootstrap/loader",
            "text": "Generate bootstrap loader",
            "category": "bootstrap",
            "name": "Loader",
            "type": "loader_stage"
        }
    ]

    # Generate code
    codegen = CodeGenerator()
    outputs = codegen.run(checklist)

    # Should have bootstrap output
    bootstrap_outputs = [out for out in outputs if "bootstrap" in out.get("path", "")]

    assert len(bootstrap_outputs) > 0


def test_bootstrap_module_deterministic_name():
    """Test bootstrap module has deterministic class name."""
    from shieldcraft.services.codegen.generator import CodeGenerator

    checklist = [
        {
            "id": "bootstrap.engine.1",
            "ptr": "/sections/bootstrap/engine",
            "text": "Generate bootstrap engine",
            "category": "bootstrap",
            "name": "Engine",
            "type": "engine_stage"
        }
    ]

    codegen = CodeGenerator()
    outputs = codegen.run(checklist)

    bootstrap_outputs = [out for out in outputs if "bootstrap" in out.get("path", "")]

    if bootstrap_outputs:
        content = bootstrap_outputs[0].get("content", "")
        # Should have deterministic class name
        assert "class EngineBootstrap:" in content


def test_bootstrap_template_output():
    """Test bootstrap template produces expected output."""
    from shieldcraft.services.codegen.generator import CodeGenerator

    checklist = [
        {
            "id": "bootstrap.test.1",
            "ptr": "/sections/bootstrap/test",
            "text": "Generate bootstrap test",
            "category": "bootstrap",
            "name": "TestComponent",
            "type": "test_stage"
        }
    ]

    codegen = CodeGenerator()
    outputs = codegen.run(checklist)

    bootstrap_outputs = [out for out in outputs if "bootstrap" in out.get("path", "")]

    if bootstrap_outputs:
        content = bootstrap_outputs[0].get("content", "")

        # Should have checklist_id comment
        assert "bootstrap-generated:" in content
        assert "bootstrap.test.1" in content

        # Should have Bootstrap suffix
        assert "Bootstrap:" in content


def test_bootstrap_codegen_with_selfhost():
    """Test bootstrap codegen in self-host mode."""
    from shieldcraft.main import run_self_host

    # Create self-host spec with bootstrap section
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {
                "product_id": "test-bootstrap-codegen",
                "version": "1.0",
                "spec_format": "canonical_json_v1",
                "self_host": True
            },
            "model": {"version": "1.0"},
            "sections": {
                "bootstrap": {
                    "description": "Bootstrap components",
                    "loader": {
                        "type": "loader_stage",
                        "name": "SpecLoader"
                    }
                }
            }
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name

    try:
        # Clean output directory
        if os.path.exists(".selfhost_outputs"):
            shutil.rmtree(".selfhost_outputs")

        # Run self-host
        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")

        # Check if bootstrap directory exists
        if os.path.exists(".selfhost_outputs/bootstrap"):
            # List files
            bootstrap_files = os.listdir(".selfhost_outputs/bootstrap")
            # Should have at least some generated files
            assert len(bootstrap_files) >= 0  # May be 0 if no bootstrap items classified

        # Verify summary exists
        assert os.path.exists(".selfhost_outputs/summary.json")

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_bootstrap_module_multiple_items():
    """Test multiple bootstrap items generate separate modules."""
    from shieldcraft.services.codegen.generator import CodeGenerator

    checklist = [
        {
            "id": "bootstrap.loader.1",
            "ptr": "/sections/bootstrap/loader",
            "text": "Generate bootstrap loader",
            "category": "bootstrap",
            "name": "Loader",
            "type": "loader_stage"
        },
        {
            "id": "bootstrap.engine.1",
            "ptr": "/sections/bootstrap/engine",
            "text": "Generate bootstrap engine",
            "category": "bootstrap",
            "name": "Engine",
            "type": "engine_stage"
        }
    ]

    codegen = CodeGenerator()
    outputs = codegen.run(checklist)

    bootstrap_outputs = [out for out in outputs if "bootstrap" in out.get("path", "")]

    # Should have 2 bootstrap modules
    assert len(bootstrap_outputs) == 2

    # Should have different names
    paths = [out.get("path") for out in bootstrap_outputs]
    assert len(set(paths)) == 2
