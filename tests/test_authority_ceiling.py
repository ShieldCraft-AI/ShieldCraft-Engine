def test_tier_a_synthesis_requires_blocker_event():
    from shieldcraft.engine import finalize_checklist, Engine

    engine = Engine(schema_path='')

    class StubContext:
        def __init__(self):
            self._events = []
        def record_event(self, gate_id, phase, outcome, message=None, evidence=None, **kwargs):
            self._events.append({'gate_id': gate_id, 'phase': phase, 'outcome': outcome, 'message': message, 'evidence': evidence})
        def get_events(self):
            return list(self._events)

    engine.checklist_context = StubContext()

    # Partial result contains a Tier A synthesized default but no corresponding BLOCKER event
    partial = {'checklist': {'items': [{ 'ptr': '/agents', 'text': 'Synthesized default for agents', 'meta': {'source': 'default', 'tier': 'A', 'synthesized_default': True}}]}}

    import pytest
    with pytest.raises(AssertionError):
        finalize_checklist(engine, partial_result=partial)


def test_tier_a_synthesis_requires_blocker_and_diagnostic():
    from shieldcraft.engine import finalize_checklist, Engine

    engine = Engine(schema_path='')

    class StubContext:
        def __init__(self):
            self._events = []
        def record_event(self, gate_id, phase, outcome, message=None, evidence=None, **kwargs):
            self._events.append({'gate_id': gate_id, 'phase': phase, 'outcome': outcome, 'message': message, 'evidence': evidence})
        def get_events(self):
            return list(self._events)

    engine.checklist_context = StubContext()

    # Simulate only a BLOCKER event recorded but no DIAGNOSTIC
    engine.checklist_context.record_event('G_SYNTHESIZED_DEFAULT_AGENTS', 'compilation', 'BLOCKER', message='Synthesized Tier A default for agents', evidence={'section': 'agents'})

    partial = {'checklist': {'items': [{ 'ptr': '/agents', 'text': 'Synthesized default for agents', 'meta': {'source': 'default', 'tier': 'A', 'synthesized_default': True}}]}}

    import pytest
    with pytest.raises(AssertionError):
        finalize_checklist(engine, partial_result=partial)


def test_refusal_requires_authority():
    from shieldcraft.engine import finalize_checklist, Engine

    engine = Engine(schema_path='')

    class StubContext:
        def __init__(self):
            self._events = []
        def record_event(self, gate_id, phase, outcome, message=None, evidence=None, **kwargs):
            self._events.append({'gate_id': gate_id, 'phase': phase, 'outcome': outcome, 'message': message, 'evidence': evidence})
        def get_events(self):
            return list(self._events)

    engine.checklist_context = StubContext()

    # Emit a REFUSAL event without authority in evidence
    engine.checklist_context.record_event('G2_GOVERNANCE_PRESENCE_CHECK', 'finalize', 'REFUSAL', message='missing governance', evidence={})

    import pytest
    with pytest.raises(AssertionError):
        finalize_checklist(engine)


def test_derived_tasks_do_not_introduce_authority():
    from shieldcraft.services.checklist.derived import infer_tasks
    item = {'ptr': '/metadata', 'id': 'p1', 'value': {}}
    derived = infer_tasks(item)
    # Derived tasks must not introduce refusal authority metadata
    for d in derived:
        assert not ((d.get('meta') or {}).get('refusal_authority')), 'Derived task introduced refusal authority'


def test_confidence_does_not_override_item_fields():
    from shieldcraft.services.guidance.checklist import enrich_with_confidence_and_evidence
    items = [{'ptr': '/sections/1', 'text': 'must do X', 'value': 'must do X'}]
    res = enrich_with_confidence_and_evidence(items)
    # confidence enrichment should only add metadata, not override core fields
    assert res[0]['text'] == 'must do X'
    assert 'confidence_meta' in res[0]
