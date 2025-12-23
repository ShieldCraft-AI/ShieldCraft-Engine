def test_tier_a_default_records_blocker_and_diagnostic():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.engine import Engine

    # Missing 'agents' should trigger a Tier A synthesized default
    spec = {"metadata": {"product_id": "x"}}
    ast = ASTBuilder().build(spec)
    engine = Engine(schema_path='')

    class StubContext:
        def __init__(self):
            self._events = []

        def record_event(self, gate_id, phase, outcome, message=None, evidence=None, **kwargs):
            self._events.append({'gate_id': gate_id, 'phase': phase, 'outcome': outcome,
                                'message': message, 'evidence': evidence})

        def get_events(self):
            return list(self._events)

    engine.checklist_context = StubContext()
    chk = ChecklistGenerator().build(spec, ast=ast, dry_run=True, engine=engine)
    items = chk.get('items', [])

    # Check synthesized item present and has meta
    synth = [it for it in items if (it.get('meta') or {}).get('synthesized_default')]
    assert any((it.get('meta') or {}).get('tier') == 'A' for it in synth)
    # Check events include a BLOCKER and a DIAGNOSTIC for synthesized default
    evs = engine.checklist_context.get_events()
    assert any(e['outcome'] == 'BLOCKER' and 'G_SYNTHESIZED_DEFAULT_AGENTS' in e['gate_id'] for e in evs)
    assert any(e['outcome'] == 'DIAGNOSTIC' and 'G_SYNTHESIZED_DEFAULT_AGENTS' in e['gate_id'] for e in evs)


def test_coercion_preserves_original_value():
    from shieldcraft.services.checklist.model import ChecklistModel
    model = ChecklistModel()
    item = {}
    ni = model.normalize_item(item)
    meta = ni.get('meta', {})
    assert meta.get('source') == 'coerced'
    assert 'original_value' in meta


def test_derived_tasks_include_derived_from():
    from shieldcraft.services.checklist.derived import infer_tasks
    item = {'ptr': '/some', 'id': 'p1', 'value': {}}
    derived = infer_tasks(item)
    assert all(d.get('meta', {}).get('derived_from') == 'p1' for d in derived if d.get('meta'))


def test_confidence_explainability_attached():
    from shieldcraft.services.guidance.checklist import enrich_with_confidence_and_evidence
    items = [{'ptr': '/sections/1', 'text': 'must do X', 'value': 'must do X'}]
    res = enrich_with_confidence_and_evidence(items)
    assert any('confidence_meta' in it for it in res)
    assert res[0]['confidence_meta']['source'] == 'heuristic:prose'


def test_invariant_safe_default_emits_diagnostic_and_event():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.engine import Engine

    spec = {"sections": [{"name": "a", "invariant": "unknown_expr()"}], "metadata": {"product_id": "p"}}
    engine = Engine(schema_path='')

    class StubContext:
        def __init__(self):
            self._events = []

        def record_event(self, gate_id, phase, outcome, message=None, evidence=None, **kwargs):
            self._events.append({'gate_id': gate_id, 'phase': phase, 'outcome': outcome,
                                'message': message, 'evidence': evidence})

        def get_events(self):
            return list(self._events)

    engine.checklist_context = StubContext()
    chk = ChecklistGenerator().build(spec, dry_run=True, engine=engine)
    items = chk.get('items', [])
    assert any(it.get('text', '').startswith('INVARIANT_SAFE_DEFAULT:') for it in items)
    evs = engine.checklist_context.get_events()
    assert any(e['outcome'] == 'DIAGNOSTIC' and e['gate_id'] == 'G_INVARIANT_SAFE_DEFAULT' for e in evs)
