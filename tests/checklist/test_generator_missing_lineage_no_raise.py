from shieldcraft.services.checklist.generator import ChecklistGenerator
from shieldcraft.engine import Engine


def test_generator_does_not_raise_on_missing_lineage_and_records_event(monkeypatch, tmp_path):
    engine = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')
    gen = ChecklistGenerator()

    # Force lineage map to be empty to simulate missing lineage
    monkeypatch.setattr('shieldcraft.services.ast.lineage.get_lineage_map', lambda ast: {})

    # Minimal spec that will produce at least one item
    spec = {"metadata": {"product_id": "test"}, "sections": {"a": {"tasks": ["must do x"]}}, "instructions": []}

    res = gen.build(spec, engine=engine)
    assert isinstance(res, dict)
    # Should not have raised and should have returned a result dict
    assert 'items' in res
    # Event should be recorded on engine context
    evs = engine.checklist_context.get_events()
    assert any(ev.get('gate_id') == 'G10_GENERATOR_PREP_MISSING' for ev in evs)
