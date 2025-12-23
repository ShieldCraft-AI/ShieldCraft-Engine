from shieldcraft.engine import _assert_semantic_invariants


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


def test_assertion_violated_for_blocked_with_refusal():
    # Simulate an explicitly malformed checklist violating BLOCKED invariant
    bad_checklist = {'items': [{'role': 'PRIMARY_CAUSE'}], 'refusal': True, 'refusal_reason': 'x'}
    try:
        _assert_semantic_invariants(bad_checklist, 'BLOCKED', gate_outcomes={})
        raise AssertionError('Expected assertion not raised')
    except AssertionError as e:
        assert 'BLOCKED outcome must not set refusal' in str(e)


def test_assertion_violated_for_success_with_primary_cause():
    bad = {'items': [{'role': 'PRIMARY_CAUSE'}], 'refusal': False}
    try:
        _assert_semantic_invariants(bad, 'SUCCESS', gate_outcomes={})
        raise AssertionError('Expected assertion not raised')
    except AssertionError as e:
        assert 'SUCCESS outcome must not contain PRIMARY_CAUSE' in str(e)


def test_assertion_violated_for_diagnostic_only_with_blocker():
    bad = {'items': [{'role': 'PRIMARY_CAUSE', 'meta': {'gate': 'G_B'}}], 'refusal': False}
    gate_outcomes = {'G_B': {'BLOCKER'}}
    try:
        _assert_semantic_invariants(bad, 'DIAGNOSTIC_ONLY', gate_outcomes=gate_outcomes)
        raise AssertionError('Expected assertion not raised')
    except AssertionError as e:
        assert 'DIAGNOSTIC_ONLY outcome must not contain BLOCKER or REFUSAL' in str(e)
