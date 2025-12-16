import json
import os
import pytest


from shieldcraft.services.spec.ingestion import ingest_spec
from shieldcraft.services.spec.normalization import CANONICAL_SPEC_FORMAT


@pytest.mark.parametrize("content,expected_normalized", [
    (open("spec/test_spec.yml").read(), True),  # YAML text
    ("plain text content", True),  # plain text
    (json.dumps({"a": 1}), True),  # JSON dict (non-DSL)
    (json.dumps([1, 2, 3]), True),  # JSON list
    ("", True),  # empty file
])
def test_ingest_spec_accepts_any_input_format(tmp_path, content, expected_normalized):
    p = tmp_path / "in"
    p.write_text(content)
    spec = ingest_spec(str(p))
    assert isinstance(spec, dict)
    # For non-native inputs we expect a normalized DSL skeleton
    md = spec.get("metadata", {})
    assert md.get("spec_format") == CANONICAL_SPEC_FORMAT
    assert md.get("normalized") is True


def test_ingest_spec_returns_existing_dsl_unchanged(tmp_path):
    p = tmp_path / "dsl.json"
    dsl = {"metadata": {"product_id": "x", "spec_format": CANONICAL_SPEC_FORMAT}, "model": {}, "sections": {}}
    p.write_text(json.dumps(dsl))
    spec = ingest_spec(str(p))
    # Already a DSL-shaped dict should be returned as-is (no wrapping)
    assert spec.get("model") == {}
    assert spec.get("sections") == {}
    assert spec.get("metadata", {}).get("spec_format") == CANONICAL_SPEC_FORMAT
