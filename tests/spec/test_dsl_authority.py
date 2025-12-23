"""Test DSL authority and contract freeze."""

import json
from pathlib import Path


def test_single_dsl_schema_exists():
    """Verify only ONE DSL schema exists under spec/schemas/."""
    schema_dir = Path("spec/schemas")
    schema_files = list(schema_dir.glob("*.schema.json"))

    assert len(schema_files) == 1, f"Expected 1 schema, found {len(schema_files)}: {schema_files}"
    assert schema_files[0].name == "se_dsl_v1.schema.json"


def test_engine_imports_canonical_loader():
    """Verify engine imports loader from src/shieldcraft/dsl/loader.py."""
    engine_file = Path("src/shieldcraft/engine.py")
    content = engine_file.read_text()

    assert "from shieldcraft.dsl.loader import load_spec" in content, \
        "Engine must import load_spec from shieldcraft.dsl.loader"


def test_schema_file_name():
    """Verify schema file name equals se_dsl_v1.schema.json."""
    schema_file = Path("spec/schemas/se_dsl_v1.schema.json")
    assert schema_file.exists(), "Schema file spec/schemas/se_dsl_v1.schema.json must exist"


def test_schema_is_frozen():
    """Verify schema has dsl_status=frozen and change_policy set."""
    schema_file = Path("spec/schemas/se_dsl_v1.schema.json")
    with open(schema_file, encoding='utf-8') as f:
        schema = json.load(f)

    assert schema.get("dsl_status") == "frozen", "Schema must have dsl_status='frozen'"
    assert "change_policy" in schema, "Schema must have change_policy field"
    assert "breaking changes require new schema version" in schema["change_policy"]
