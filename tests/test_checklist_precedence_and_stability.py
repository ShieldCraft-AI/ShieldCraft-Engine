import json
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


def test_mixed_refusal_and_blocker_yields_refusal():
    e = E()
    e.checklist_context.record_event('G_B', 'gen', 'BLOCKER')
    e.checklist_context.record_event('G_R', 'post', 'REFUSAL')
    r = finalize_checklist(e)
    assert r['primary_outcome'] == 'REFUSAL'


def test_blocker_and_diagnostic_yields_blocked():
    e = E()
    e.checklist_context.record_event('G_B', 'gen', 'BLOCKER')
    e.checklist_context.record_event('G_D', 'preflight', 'DIAGNOSTIC')
    r = finalize_checklist(e)
    assert r['primary_outcome'] == 'BLOCKED'


def test_only_diagnostic_events_yield_diagnostic_only():
    e = E()
    e.checklist_context.record_event('G_D1', 'preflight', 'DIAGNOSTIC')
    e.checklist_context.record_event('G_D2', 'preflight', 'DIAGNOSTIC')
    r = finalize_checklist(e)
    assert r['primary_outcome'] == 'DIAGNOSTIC_ONLY'


def test_order_independence_of_outcome():
    e1 = E()
    e1.checklist_context.record_event('G_B', 'gen', 'BLOCKER')
    e1.checklist_context.record_event('G_R', 'post', 'REFUSAL')
    r1 = finalize_checklist(e1)

    e2 = E()
    e2.checklist_context.record_event('G_R', 'post', 'REFUSAL')
    e2.checklist_context.record_event('G_B', 'gen', 'BLOCKER')
    r2 = finalize_checklist(e2)

    assert r1['primary_outcome'] == r2['primary_outcome'] == 'REFUSAL'


def test_primary_cause_selection_tiebreaks():
    # Two BLOCKERs, choose lowest gate_id lexicographically
    e = E()
    e.checklist_context.record_event('G_Z', 'gen', 'BLOCKER')
    e.checklist_context.record_event('G_A', 'gen', 'BLOCKER')
    r = finalize_checklist(e)
    primary_gates = [
        it.get(
            'meta',
            {}).get('gate') for it in r['checklist'].get(
            'items',
            []) if it.get('role') == 'PRIMARY_CAUSE']
    assert primary_gates == ['G_A']


def test_primary_cause_earliest_event_if_gate_ties():
    # Simulate two events with same gate id (duplicate events) but different occurrence
    e = E()
    e.checklist_context.record_event('G_TIE', 'phase1', 'REFUSAL')
    e.checklist_context.record_event('G_TIE', 'phase2', 'REFUSAL')
    r = finalize_checklist(e)
    primary = [it for it in r['checklist'].get('items', []) if it.get('role') == 'PRIMARY_CAUSE'][0]
    assert primary.get('meta', {}).get('phase') == 'phase1'


def test_semantic_output_stability():
    e = E()
    e.checklist_context.record_event('G_B', 'gen', 'BLOCKER')
    e.checklist_context.record_event('G_D', 'preflight', 'DIAGNOSTIC')
    r1 = finalize_checklist(e)
    r2 = finalize_checklist(e)
    s1 = json.dumps(r1, sort_keys=True)
    s2 = json.dumps(r2, sort_keys=True)
    assert s1 == s2
