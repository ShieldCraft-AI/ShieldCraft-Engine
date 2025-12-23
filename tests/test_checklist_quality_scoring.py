def test_quality_score_penalizes_blockers_and_synthesized_defaults():
    from shieldcraft.services.checklist.quality import compute_checklist_quality
    items = [
        {'text': 'SPEC MISSING: Missing template section: agents (Tier A)', 'meta': {
            'tier': 'A', 'synthesized_default': True}},
        {'text': 'SPEC INSUFFICIENT: No agents declared', 'meta': {'insufficiency': 'NO_AGENTS'}},
    ]
    q = compute_checklist_quality(items, synthesized_count=1, insufficiency_count=1)
    assert isinstance(q, int)
    assert q < 100
    assert q >= 0


def test_finalize_attaches_quality_and_appends_diagnostic():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.engine import Engine

    spec = {"metadata": {"product_id": "x"}}
    ast = ASTBuilder().build(spec)
    engine = Engine(schema_path='')

    class StubContext:
        def __init__(self):
            self._events = []

        def record_event(self, gate_id, phase, outcome, message=None, evidence=None, **kwargs):
            # Normalize into dict similar to production context
            ev = {
                'gate_id': gate_id,
                'phase': phase,
                'outcome': outcome,
                'message': message,
                'evidence': evidence or {},
            }
            self._events.append(ev)

        def get_events(self):
            return list(self._events)

    engine.checklist_context = StubContext()
    chk = ChecklistGenerator().build(spec, ast=ast, dry_run=True, engine=engine)
    # finalize_checklist would normally compute quality; simulate by calling finalize_checklist
    from shieldcraft.engine import finalize_checklist
    res = finalize_checklist(
        engine,
        partial_result={
            'checklist': {
                'items': chk.get(
                    'items',
                    []),
                'events': engine.checklist_context.get_events(),
                'emitted': True}})
    assert 'meta' in res['checklist'] and 'checklist_quality' in res['checklist']['meta']
    q = res['checklist']['meta']['checklist_quality']
    assert isinstance(q, int)
    # If low, a diagnostic item should be appended
    if q < 60:
        assert any(it.get('text', '').startswith('CHECKLIST QUALITY LOW') for it in res['checklist']['items'])
