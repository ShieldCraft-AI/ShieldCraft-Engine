from shieldcraft.services.checklist.generator import ChecklistGenerator
from shieldcraft.engine import Engine


def test_generator_returns_partial_result_on_test_gate_failure(monkeypatch):
    engine = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')
    gen = ChecklistGenerator()

    # Force enforce_tests_attached to raise
    def fake_enforce_tests_attached(decorated):
        raise RuntimeError('tests missing')
    monkeypatch.setattr('shieldcraft.services.validator.test_gate.enforce_tests_attached', fake_enforce_tests_attached)

    spec = {"metadata": {"product_id": "test"}, "instructions": [], "sections": {"s": {"tasks": ["do x"]}}}

    res = gen.build(spec, run_test_gate=True, engine=engine)
    assert isinstance(res, dict)
    assert res.get('valid') is False
    evs = engine.checklist_context.get_events()
    assert any(ev.get('gate_id') == 'G11_RUN_TEST_GATE' for ev in evs)
