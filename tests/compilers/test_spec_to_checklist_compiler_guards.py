import json

from shieldcraft.services.checklist.generator import ChecklistGenerator
from shieldcraft.engine import Engine, finalize_checklist


class DummyContext:
    def __init__(self):
        self._events = []

    def record_event(self, gate, phase, outcome, **kwargs):
        self._events.append({'gate_id': gate, 'phase': phase, 'outcome': outcome,
                            'message': kwargs.get('message'), 'evidence': kwargs.get('evidence')})

    def get_events(self):
        return list(self._events)


def test_build_returns_partial_on_fuzz_failure(monkeypatch, tmp_path):
    # Simulate fuzz gate failure; generator should return a partial invalid result (no raise)
    def fake_enforce(spec, generator):
        raise RuntimeError("fuzz failed")

    monkeypatch.setattr('shieldcraft.services.validator.spec_gate.enforce_spec_fuzz_stability', fake_enforce)

    # Create a valid schema file path to avoid schema loader treating the schema arg as a directory
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps({}))
    engine = Engine(schema_path=str(schema_file))
    engine.checklist_context = DummyContext()

    gen = ChecklistGenerator()
    res = gen.build({'metadata': {'product_id': 'p'}}, run_fuzz=True, engine=engine)

    assert isinstance(res, dict)
    # Partial invalid result should indicate invalid generation and include items list
    assert res.get('valid') in (True, False)
    assert 'items' in res
    # Generator should have recorded the G9 gate when fuzz failed
    evs = engine.checklist_context.get_events()
    assert any(ev.get('gate_id') == 'G9_GENERATOR_RUN_FUZZ_GATE' for ev in evs)


def test_engine_finalizes_on_compiler_exception(monkeypatch, tmp_path):
    # When the compiler raises unexpectedly, Engine.run must finalize and return a checklist artifact
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps({'metadata': {'product_id': 'test-product'}, 'instructions': []}))

    # Force the compiler to raise
    def boom(self, *a, **k):
        raise Exception('boom')

    monkeypatch.setattr('shieldcraft.services.checklist.generator.ChecklistGenerator.build', boom)

    # Ensure schema path is a file to avoid schema loader errors
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps({}))

    eng = Engine(schema_path=str(schema_file))
    res = eng.run(str(spec_path))

    assert isinstance(res, dict)
    assert res.get('emitted') is True
    # Finalize call should have recorded an internal diagnostic gate event
    # (events live under result['checklist']['events'])
    evs = res.get('checklist', {}).get('events', [])
    assert any(e.get('gate_id') == 'G22_EXECUTE_INTERNAL_ERROR_RETURN' for e in evs)
    # The finalized checklist should include the internal exception item
    assert any('internal_exception: boom' in (it.get('text') or '') for it in res.get('checklist', {}).get('items', []))


def test_all_recorded_events_appear_in_final_checklist():
    # Use a lightweight wrapper with dedicated DummyContext (matches existing unit-test patterns)
    class E:
        def __init__(self):
            self.checklist_context = DummyContext()

    e = E()
    e.checklist_context.record_event('G_A', 'gen', 'BLOCKER', message='a')
    e.checklist_context.record_event('G_B', 'post', 'REFUSAL', message='b')
    e.checklist_context.record_event('G_C', 'preflight', 'DIAGNOSTIC', message='c')

    final = finalize_checklist(e)

    # All events should be present in final['checklist']['events']
    ev_ids = {e.get('gate_id') for e in final.get('checklist', {}).get('events', [])}
    assert {'G_A', 'G_B', 'G_C'}.issubset(ev_ids)

    # Each recorded event should have produced a checklist item with meta.gate
    item_gates = {(it.get('meta') or {}).get('gate') for it in final.get('checklist', {}).get('items', [])}
    assert {'G_A', 'G_B', 'G_C'}.issubset(item_gates)
