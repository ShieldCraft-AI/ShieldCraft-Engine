from shieldcraft.services.checklist.model import ChecklistModel
from shieldcraft.services.checklist.context import ChecklistContext, set_global_context


def test_model_validation_records_G21_and_does_not_raise():
    ctx = ChecklistContext()
    set_global_context(ctx)

    model = ChecklistModel()
    item = {"text": "sample"}  # missing ptr

    res = model.normalize_item(item)
    assert isinstance(res, dict)
    assert res.get('quality_status') == 'INVALID'
    evs = ctx.get_events()
    assert any(ev.get('gate_id') == 'G21_CHECKLIST_MODEL_VALIDATION_ERRORS' for ev in evs)
