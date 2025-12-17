def test_refusal_event_contains_authority_and_propagates():
    from shieldcraft.services.governance.refusal_authority import record_refusal_event
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
    # Use G2 which maps to governance authority
    record_refusal_event(engine.checklist_context, 'G2_GOVERNANCE_PRESENCE_CHECK', 'preflight', message='missing governance doc', trigger='missing_authority', scope='/governance', justification='gov_missing')
    res = finalize_checklist(engine)
    assert res['refusal'] is True
    assert res['checklist'].get('refusal_reason') is not None
    # Authority must appear in the event evidence and be reflected in final checklist (as refusal_authority)
    assert any(e.get('evidence', {}).get('refusal', {}).get('authority') == 'governance' for e in engine.checklist_context.get_events())
    # finalize_checklist should expose the authority in the checklist
    assert res['checklist'].get('refusal_authority') == 'governance'


def test_refusal_without_authority_fails():
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
    # Directly record a REFUSAL without authority metadata
    engine.checklist_context.record_event('G2_GOVERNANCE_PRESENCE_CHECK', 'preflight', 'REFUSAL', message='missing governance doc')
    import pytest
    with pytest.raises(AssertionError):
        finalize_checklist(engine)


def test_paired_diagnostic_on_missing_authority():
    from shieldcraft.services.governance.refusal_authority import record_refusal_event
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
    record_refusal_event(engine.checklist_context, 'G2_GOVERNANCE_PRESENCE_CHECK', 'preflight', message='missing governance doc', trigger='missing_authority', scope='/governance', justification='gov_missing')
    res = finalize_checklist(engine)
    items = res['checklist']['items']
    assert any(it.get('text', '').startswith('MISSING_AUTHORITY:') or it.get('text','').startswith('REFUSAL_DIAG:') for it in items)
