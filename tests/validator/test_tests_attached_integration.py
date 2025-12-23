import pytest

from shieldcraft.engine import Engine
from shieldcraft.services.validator.tests_attached_validator import ProductInvariantFailure


def test_preflight_halts_on_missing_test_refs(monkeypatch):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Monkeypatch checklist generation to return missing test_refs
    def fake_build(spec, ast=None, **kwargs):
        return {"items": [{"id": "x1", "ptr": "/x/1", "text": "t1"}]}

    monkeypatch.setattr(engine.checklist_gen, "build", fake_build)

    import json
    spec = json.load(open('spec/se_dsl_v1.spec.json', encoding='utf-8'))

    # Enable TAC enforcement for this test via env var
    monkeypatch.setenv("SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT", "1")

    with pytest.raises(ProductInvariantFailure):
        engine.preflight(spec)
