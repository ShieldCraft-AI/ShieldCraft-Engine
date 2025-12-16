import json
import os

from shieldcraft.engine import Engine
from shieldcraft.services.checklist.context import ChecklistContext, set_global_context
from shieldcraft.services.checklist.model import ChecklistModel


def test_schema_validation_records_G4(tmp_path):
    # Write an invalid spec (missing required metadata) to a temp file
    spec_path = tmp_path / "bad_spec.json"
    spec_path.write_text(json.dumps({}))

    eng = Engine(schema_path="src/shieldcraft/dsl/schema/se_dsl.schema.json")
    # Ensure context present
    assert eng.checklist_context is not None
    res = eng.run(str(spec_path))
    assert res.get("type") == "schema_error"
    events = eng.checklist_context.get_events()
    assert any(e.get("gate_id") == "G4_SCHEMA_VALIDATION" for e in events)


def test_model_missing_spec_pointer_records_G21():
    ctx = ChecklistContext()
    set_global_context(ctx)
    model = ChecklistModel()
    try:
        model.normalize_item({})
    except Exception:
        pass
    evs = ctx.get_events()
    assert any(e.get("gate_id") == "G21_CHECKLIST_MODEL_VALIDATION_ERRORS" for e in evs)
