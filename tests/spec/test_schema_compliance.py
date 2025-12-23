"""Test schema compliance."""
import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError


def test_spec_validates_against_schema():
    """Test that se_dsl_v1.spec.json validates against se_dsl.schema.json."""
    # Load schema
    schema_path = Path(__file__).parent.parent.parent / "src/shieldcraft/dsl/schema/se_dsl.schema.json"
    with open(schema_path, encoding='utf-8') as f:
        schema = json.load(f)

    # Load spec
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    # Validate
    try:
        validate(instance=spec, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Spec validation failed: {e.message}")


def test_metadata_product_id_pattern():
    """Test that product_id matches required pattern."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    product_id = spec["metadata"]["product_id"]

    # Should match ^[a-z0-9_]+$
    import re
    assert re.match(r"^[a-z0-9_]+$", product_id), f"product_id '{product_id}' does not match pattern"


def test_unique_component_ids():
    """Test that model.components have unique IDs."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    component_ids = [c["id"] for c in spec["model"]["components"]]

    assert len(component_ids) == len(set(component_ids)), f"Duplicate component IDs found: {component_ids}"


def test_unique_section_ids():
    """Test that sections have unique IDs."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    section_ids = [s["id"] for s in spec["sections"]]

    assert len(section_ids) == len(set(section_ids)), f"Duplicate section IDs found: {section_ids}"


def test_required_metadata_fields():
    """Test that required metadata fields are present."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    metadata = spec["metadata"]

    assert "product_id" in metadata, "metadata.product_id is required"
    assert "spec_version" in metadata, "metadata.spec_version is required"


def test_component_dependencies_structure():
    """Test that component dependencies have required fields."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    dependencies = spec["model"]["dependencies"]

    for dep in dependencies:
        assert "from" in dep, f"Dependency missing 'from': {dep}"
        assert "to" in dep, f"Dependency missing 'to': {dep}"


def test_task_structure():
    """Test that tasks have required fields."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    for section in spec["sections"]:
        for task in section.get("tasks", []):
            assert "id" in task, f"Task missing 'id' in section {section['id']}"
            assert "type" in task, f"Task missing 'type' in section {section['id']}"
            assert "ptr" in task, f"Task missing 'ptr' in section {section['id']}"
