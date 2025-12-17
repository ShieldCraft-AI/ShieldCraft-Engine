def test_tier_enforcement_function_exists_and_returns_items():
    from shieldcraft.services.checklist.tier_enforcement import enforce_tiers

    class StubContext:
        def __init__(self):
            self._events = []
        def record_event(self, gid, phase, outcome, message=None, evidence=None, **kwargs):
            self._events.append({'gate_id': gid, 'phase': phase, 'outcome': outcome, 'message': message, 'evidence': evidence})

    ctx = StubContext()
    items = enforce_tiers({}, context=ctx)
    assert isinstance(items, list)
    assert any('/agents' == it.get('ptr') for it in items)
    assert any(ev['gate_id'].startswith('G_TIER_A_MISSING') or ev['gate_id'].startswith('G_TIER_B_MISSING') for ev in ctx._events)


def test_default_synthesis_function_is_authoritative():
    from shieldcraft.services.spec.defaults import synthesize_missing_spec_fields
    assert callable(synthesize_missing_spec_fields)


def test_finalized_checklist_includes_quality_meta():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.engine import Engine, finalize_checklist

    spec = {"metadata": {"product_id": "x"}}
    ast = ASTBuilder().build(spec)
    engine = Engine(schema_path='')

    class StubContext:
        def __init__(self):
            self._events = []
        def record_event(self, gate_id, phase, outcome, message=None, evidence=None, **kwargs):
            self._events.append({'gate_id': gate_id, 'phase': phase, 'outcome': outcome, 'message': message, 'evidence': evidence})
        def get_events(self):
            return list(self._events)

    engine.checklist_context = StubContext()
    chk = ChecklistGenerator().build(spec, ast=ast, dry_run=True, engine=engine)
    res = finalize_checklist(engine, partial_result={'checklist': {'items': chk.get('items', []), 'events': engine.checklist_context.get_events(), 'emitted': True}})
    assert 'meta' in res['checklist'] and 'checklist_quality' in res['checklist']['meta']
