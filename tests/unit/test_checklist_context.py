
from shieldcraft.engine import Engine
from shieldcraft.services.checklist.context import ChecklistContext


def test_engine_initializes_checklist_context(tmp_path):
    eng = Engine(schema_path=str(tmp_path))
    assert hasattr(eng, 'checklist_context')
    assert isinstance(eng.checklist_context, (ChecklistContext, type(None)))


def test_context_record_and_get_events():
    ctx = ChecklistContext()
    ctx.record_event('G1', 'preflight', 'REFUSAL', message='test', evidence={'x': 1})
    evs = ctx.get_events()
    assert len(evs) == 1
    assert evs[0]['gate_id'] == 'G1'
    assert evs[0]['phase'] == 'preflight'
    assert evs[0]['outcome'] == 'REFUSAL'
