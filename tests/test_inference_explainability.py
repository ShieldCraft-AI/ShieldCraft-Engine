def test_explainability_contract_doc_exists():
    import pathlib
    # Use repo root (parents[1]) to locate docs inside the repository
    p = pathlib.Path(__file__).resolve().parents[1] / 'docs' / 'governance' / 'INFERENCE_EXPLAINABILITY_CONTRACT.md'
    assert p.exists()


def test_synthesized_items_have_explainability():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.engine import Engine

    spec = {"metadata": {"product_id": "testprod"}, "pipeline": {"states": ["ingest_spec"]}}
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
    synthesized = [it for it in items if (it.get('meta') or {}).get('synthesized_default')]
    assert synthesized, 'No synthesized items found'
    for it in synthesized:
        meta = it.get('meta') or {}
        assert meta.get('source') in ('default', 'explicit', 'derived', 'coerced', 'inferred')
        assert meta.get('justification') is not None
        assert meta.get('inference_type') in ('none', 'safe_default', 'heuristic', 'structural', 'fallback')


def test_coercion_explainability_on_missing_pointer():
    from shieldcraft.services.checklist.model import ChecklistModel
    model = ChecklistModel()
    item = {'text': 'x'}
    ni = model.normalize_item(item)
    assert ni.get('meta', {}).get('source') == 'coerced'
    assert 'missing_spec_pointer' in ni.get('meta', {}).get('justification')
    assert 'original_value' in ni.get('meta', {})


def test_derived_tasks_have_explainability():
    from shieldcraft.services.checklist.derived import infer_tasks
    item = {'ptr': '/metadata', 'id': 'i1', 'value': {}}  # missing product_id -> derived tasks
    derived = infer_tasks(item)
    has_set_product = any(
        d for d in derived if d.get(
            'meta',
            {}).get(
            'justification',
            '').startswith('missing_metadata_field'))
    assert has_set_product
    # Derived tasks for missing metadata fields must record parent provenance
    for d in derived:
        if d.get('meta', {}).get('justification', '').startswith('missing_metadata_field'):
            assert d.get('meta', {}).get('derived_from') == 'i1'


def test_coercion_preserves_original_id_and_meta():
    from shieldcraft.services.checklist.model import ChecklistModel
    model = ChecklistModel()
    # id not string
    item = {'ptr': '/x', 'id': 123, 'text': 'x'}
    ni = model.normalize_item(item)
    assert ni.get('meta', {}).get('original_value') == 123

    # meta not dict
    item2 = {'ptr': '/y', 'id': 'i2', 'meta': 'not-a-dict', 'text': 'y'}
    ni2 = model.normalize_item(item2)
    assert ni2.get('meta', {}).get('original_value') == 'not-a-dict'


def test_invariant_default_explainability():
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.ast.builder import ASTBuilder
    from shieldcraft.engine import Engine

    spec = {"metadata": {"product_id": "x"}, "sections": [{"name": "a", "must": "count(/agents) > 0"}], "agents": []}
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
    found = False
    for it in items:
        invs = (it.get('meta') or {}).get('invariant_results', [])
        for inv in invs:
            if inv.get('explainability'):
                found = True
    assert found, 'Invariant default explainability not attached'


def test_refusal_masking_adds_diagnostic_item():
    from shieldcraft.engine import finalize_checklist, Engine
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
    from shieldcraft.services.governance.refusal_authority import record_refusal_event
    record_refusal_event(
        engine.checklist_context,
        'G2_GOVERNANCE_PRESENCE_CHECK',
        'preflight',
        message='missing governance doc',
        trigger='missing_authority',
        scope='/governance',
        justification='gov_missing')
    res = finalize_checklist(engine)
    items = res['checklist']['items']
    assert any(it.get('text', '').startswith('REFUSAL_DIAG:') for it in items)
