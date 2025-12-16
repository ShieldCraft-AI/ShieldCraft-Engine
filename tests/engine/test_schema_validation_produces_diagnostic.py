import json
import tempfile
from shieldcraft.engine import Engine
import importlib


def test_schema_validation_records_G4_and_emits_diagnostic(tmp_path, monkeypatch):
    engine = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')

    # Monkeypatch validate_spec_against_schema to return invalid
    monkeypatch.setattr('shieldcraft.engine.validate_spec_against_schema', lambda spec, schema_path: (False, ['schema_missing']))

    # Create a temporary spec file
    spec_path = tmp_path / 'bad_spec.json'
    spec_path.write_text(json.dumps({"metadata": {}}))

    res = engine.run(str(spec_path))
    assert isinstance(res, dict)
    cl = res.get('checklist', {})
    evs = cl.get('events', [])
    assert any(ev.get('gate_id') == 'G4_SCHEMA_VALIDATION' for ev in evs)
    # Ensure DIAGNOSTIC items are translated into checklist items
    items = cl.get('items', [])
    assert any('G4_SCHEMA_VALIDATION' in it.get('text', '') for it in items)
