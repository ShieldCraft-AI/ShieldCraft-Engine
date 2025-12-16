from shieldcraft.engine import finalize_checklist, Engine
import pytest


@pytest.mark.parametrize("gate,outcome,phase", [
    ("G9_GENERATOR_PREP", "DIAGNOSTIC", "generation"),
    ("G10_GENERATOR_PREP_MISSING", "REFUSAL", "generation"),
    ("G11_GENERATOR_PREP_INVALID", "BLOCKER", "generation"),
    ("G13_GENERATION_CONTRACT_FAILED", "BLOCKER", "generation"),
    ("G16_MINIMALITY_INVARIANT_FAILED", "REFUSAL", "post_generation"),
    ("G17_EXECUTION_CYCLE_DETECTED", "REFUSAL", "post_generation"),
    ("G18_MISSING_ARTIFACT_PRODUCER", "REFUSAL", "post_generation"),
    ("G19_PRIORITY_VIOLATION_DETECTED", "REFUSAL", "post_generation"),
    ("G20_QUALITY_GATE_FAILED", "REFUSAL", "post_generation"),
])
def test_finalize_checklist_translates_events(monkeypatch, gate, outcome, phase):
    engine = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')
    # Record event via context
    engine.checklist_context.record_event(gate, phase, outcome, message=f"test {gate}")

    res = finalize_checklist(engine, partial_result=None)
    cl = res.get('checklist', {})
    assert cl.get('emitted') is True
    # Check the event turned into an item
    items = cl.get('items', [])
    assert any((it.get('meta', {}).get('gate') == gate) for it in items)
    # If outcome was REFUSAL, finalize_checklist should set refusal flag
    if outcome == 'REFUSAL':
        assert cl.get('refusal') is True
    else:
        assert cl.get('refusal') is not True
