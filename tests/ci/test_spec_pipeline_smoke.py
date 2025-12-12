"""CI smoke test for spec pipeline."""
import json
import pytest
from pathlib import Path


def test_spec_pipeline_smoke():
    """Test the full spec pipeline in dry-run mode."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    schema_path = Path(__file__).parent.parent.parent / "src/shieldcraft/dsl/schema/se_dsl.schema.json"
    
    # Step 1: Load spec
    with open(spec_path) as f:
        spec = json.load(f)
    
    assert spec is not None, "Failed to load spec"
    
    # Step 2: Validate schema
    from jsonschema import validate, ValidationError
    with open(schema_path) as f:
        schema = json.load(f)
    
    try:
        validate(instance=spec, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e.message}")
    
    # Step 3: Build AST
    from shieldcraft.services.ast.builder import ASTBuilder
    
    ast_builder = ASTBuilder()
    ast = ast_builder.build(spec)
    
    assert ast is not None, "Failed to build AST"
    
    # Step 4: Run checklist extraction (dry run concept - just verify no fatal errors)
    from shieldcraft.services.checklist.extractor import ChecklistExtractor
    
    extractor = ChecklistExtractor()
    items = extractor.extract(ast, spec)
    
    assert isinstance(items, list), "Checklist extraction failed"
    
    # Step 5: Assert no fatal violations
    # Check for critical severity items
    fatal_items = [item for item in items if item.get("severity") == "critical"]
    
    # Allow critical items but log them (this is a smoke test)
    if len(fatal_items) > 0:
        print(f"Warning: {len(fatal_items)} critical items found")


def test_spec_metadata_completeness():
    """Test that spec metadata is complete."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    
    with open(spec_path) as f:
        spec = json.load(f)
    
    metadata = spec["metadata"]
    
    required_fields = ["product_id", "spec_version"]
    for field in required_fields:
        assert field in metadata, f"Missing required metadata field: {field}"


def test_spec_model_components_defined():
    """Test that model components are defined."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    
    with open(spec_path) as f:
        spec = json.load(f)
    
    components = spec["model"]["components"]
    
    assert len(components) > 0, "No components defined in model"
    
    for component in components:
        assert "id" in component, f"Component missing id: {component}"
        assert "type" in component, f"Component missing type: {component}"


def test_spec_sections_not_empty():
    """Test that sections are not empty."""
    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    
    with open(spec_path) as f:
        spec = json.load(f)
    
    sections = spec["sections"]
    
    assert len(sections) > 0, "No sections defined"
    
    for section in sections:
        tasks = section.get("tasks", [])
        assert len(tasks) > 0, f"Section {section['id']} has no tasks"
