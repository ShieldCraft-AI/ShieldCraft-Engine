def test_spec_sufficiency_finds_missing_agents_and_artifacts():
    from shieldcraft.services.spec.analysis import check_spec_sufficiency
    spec = {"metadata": {"product_id": "x"}}
    findings = check_spec_sufficiency(spec)
    codes = {f['code'] for f in findings}
    assert 'NO_AGENTS' in codes
    assert 'NO_ARTIFACTS' in codes


def test_generator_includes_insufficiency_items():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.engine import Engine

    spec = {"metadata": {"product_id": "x"}}
    ast = ASTBuilder().build(spec)
    engine = Engine(schema_path='')

    class StubContext:
        def __init__(self):
            self._events = []

        def record_event(self, *args, **kwargs):
            self._events.append((args, kwargs))

        def get_events(self):
            return list(self._events)

    engine.checklist_context = StubContext()
    chk = ChecklistGenerator().build(spec, ast=ast, dry_run=True, engine=engine)
    items = chk.get('items', [])
    assert any(it['text'].startswith('SPEC INSUFFICIENT') for it in items)
    recs = engine.checklist_context._events
    assert any('G_SPEC_INSUFFICIENCY_NO_AGENTS' in a[0] for a in recs)
