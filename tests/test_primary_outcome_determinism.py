from shieldcraft.services.checklist.outcome import derive_primary_outcome


def test_refusal_precedence_and_blocking_reasons_order():
    checklist = {'items': []}
    evs1 = [
        {'gate_id': 'g1', 'outcome': 'DIAGNOSTIC', 'message': 'info'},
        {'gate_id': 'g2', 'outcome': 'REFUSAL', 'message': 'fatal'}
    ]
    evs2 = list(reversed(evs1))

    r1 = derive_primary_outcome(checklist, evs1)
    r2 = derive_primary_outcome(checklist, evs2)

    assert r1['primary_outcome'] == 'REFUSAL'
    assert r2['primary_outcome'] == 'REFUSAL'
    assert 'fatal' in r1['blocking_reasons']
    assert r1['blocking_reasons'] == r2['blocking_reasons']


def test_blocker_precedence_over_action_and_persona_ignored():
    checklist = {'items': [{'confidence': 'high'}]}
    evs = [
        {'gate_id': 'g1', 'outcome': 'BLOCKER', 'message': 'blocked'},
        {'persona_id': 'p1', 'outcome': 'REFUSAL', 'message': 'persona_refusal'}
    ]
    r = derive_primary_outcome(checklist, evs)
    assert r['primary_outcome'] == 'BLOCKED'
    assert not r['refusal']
    assert 'blocked' in r['blocking_reasons']


def test_action_vs_diagnostic_by_confidence():
    high_checklist = {'items': [{'confidence': 'high'}]}
    low_checklist = {'items': [{'confidence': 'low'}]}
    r_high = derive_primary_outcome(high_checklist, [])
    r_low = derive_primary_outcome(low_checklist, [])
    assert r_high['primary_outcome'] == 'ACTION'
    assert r_low['primary_outcome'] == 'DIAGNOSTIC'
    assert r_high['confidence_level'] == 'high'
    assert r_low['confidence_level'] == 'low'
