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


def _roles(result):
    return [it.get('role') for it in result['checklist'].get('items', [])]


def _primary_gates(result):
    return [
        it.get(
            'meta',
            {}).get('gate') for it in result['checklist'].get(
            'items',
            []) if it.get('role') == 'PRIMARY_CAUSE']


def test_multiple_blockers_single_primary_cause():
    engine = E()
    engine.checklist_context.record_event('G_A', 'gen', 'BLOCKER')
    engine.checklist_context.record_event('G_B', 'gen', 'BLOCKER')
    res = finalize_checklist(engine)
    assert res['primary_outcome'] == 'BLOCKED'
    roles = _roles(res)
    assert roles.count('PRIMARY_CAUSE') == 1
    assert roles.count('CONTRIBUTING_BLOCKER') == 1


def test_refusal_primary_cause_maps_to_refusal_event():
    engine = E()
    engine.checklist_context.record_event('G_X', 'post', 'REFUSAL')
    engine.checklist_context.record_event('G_A', 'gen', 'BLOCKER')
    res = finalize_checklist(engine)
    assert res['primary_outcome'] == 'REFUSAL'
    primary_gates = _primary_gates(res)
    assert any(g in ('G_X',) for g in primary_gates)
    assert res['refusal'] is True


def test_diagnostic_only_primary_and_other_informational():
    engine = E()
    engine.checklist_context.record_event('G_D1', 'preflight', 'DIAGNOSTIC')
    engine.checklist_context.record_event('G_D2', 'preflight', 'DIAGNOSTIC')
    res = finalize_checklist(engine)
    assert res['primary_outcome'] == 'DIAGNOSTIC_ONLY'
    roles = [it.get('role') for it in res['checklist'].get('items', [])]
    # Exactly one PRIMARY_CAUSE among diagnostic items, others informational
    assert roles.count('PRIMARY_CAUSE') == 1
    # No SECONDARY_DIAGNOSTIC in DIAGNOSTIC_ONLY outcome
    assert 'SECONDARY_DIAGNOSTIC' not in roles


def test_role_assignment_is_deterministic_order_independent():
    # Record events in different order; primary gate selection should be deterministic
    engine1 = E()
    engine1.checklist_context.record_event('G_B', 'gen', 'BLOCKER')
    engine1.checklist_context.record_event('G_A', 'gen', 'BLOCKER')
    res1 = finalize_checklist(engine1)

    engine2 = E()
    engine2.checklist_context.record_event('G_A', 'gen', 'BLOCKER')
    engine2.checklist_context.record_event('G_B', 'gen', 'BLOCKER')
    res2 = finalize_checklist(engine2)

    assert _primary_gates(res1) == _primary_gates(res2)
