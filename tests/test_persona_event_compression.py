from shieldcraft.engine import finalize_checklist


class DummyContext:
    def __init__(self):
        self._events = []

    def record_event(self, gate_id, phase, outcome, message=None, evidence=None):
        self._events.append({
            'gate_id': gate_id,
            'phase': phase,
            'outcome': outcome,
            'message': message,
            'evidence': evidence,
        })

    def get_events(self):
        return list(self._events)


class E:
    def __init__(self):
        self.checklist_context = DummyContext()


def test_persona_event_compression_primary_veto():
    e = E()
    # Set up persona events on engine
    e._persona_events = [
        {'persona_id': 'p1', 'capability': 'veto', 'phase': 'preflight', 'payload_ref': 'x', 'severity': 'low'},
        {'persona_id': 'p2', 'capability': 'veto', 'phase': 'preflight', 'payload_ref': 'y', 'severity': 'high'},
    ]
    res = finalize_checklist(e)
    ps = res['checklist'].get('persona_summary', {})
    # primary persona should be deterministic (lowest persona_id among vetoes -> p1)
    assert ps.get('primary_persona') == 'p1'
    assert ps.get('primary_capability') == 'veto'
    assert isinstance(ps.get('events'), list)


def test_persona_event_compression_annotations():
    e = E()
    e._persona_events = [
        {'persona_id': 'pa', 'capability': 'annotate', 'phase': 'generation', 'payload_ref': 'm', 'severity': 'info'},
        {'persona_id': 'pb', 'capability': 'decision', 'phase': 'generation', 'payload_ref': 'd', 'severity': 'info'},
    ]
    res = finalize_checklist(e)
    ps = res['checklist'].get('persona_summary', {})
    assert ps.get('primary_persona') == 'pa' or ps.get('primary_persona') == 'pb'
    assert len(ps.get('events', [])) == 2
