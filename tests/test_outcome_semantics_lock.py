import copy
from unittest.mock import patch

from shieldcraft.services.checklist.outcome import derive_primary_outcome
from shieldcraft.engine import finalize_checklist, Engine


def _sample_events():
    return [
        {'gate_id': 'G1', 'outcome': 'BLOCKER', 'message': 'b1'},
        {'gate_id': 'G2', 'outcome': 'REFUSAL', 'message': 'r1'},
        {'gate_id': 'G3', 'outcome': 'DIAGNOSTIC', 'message': 'd1'},
    ]


def _sample_items():
    return [
        {'ptr': '/', 'text': 'G1: b1', 'meta': {'gate': 'G1'}, 'confidence': 'low'},
        {'ptr': '/', 'text': 'G2: r1', 'meta': {'gate': 'G2'}, 'confidence': 'high'},
    ]


def test_event_order_independence_and_blocking_reasons_sorted():
    evs = _sample_events()
    # compute with original order
    out1 = derive_primary_outcome({'items': _sample_items()}, evs)
    # reverse order
    evs_rev = list(reversed(evs))
    out2 = derive_primary_outcome({'items': _sample_items()}, evs_rev)
    assert out1['primary_outcome'] == out2['primary_outcome']
    assert out1['refusal'] == out2['refusal']
    # blocking_reasons should be deterministically sorted and identical
    assert out1['blocking_reasons'] == out2['blocking_reasons']


def test_items_order_independence_and_confidence_agg():
    items = _sample_items()
    out1 = derive_primary_outcome({'items': items}, [])
    items_rev = list(reversed(items))
    out2 = derive_primary_outcome({'items': items_rev}, [])
    assert out1['confidence_level'] == out2['confidence_level']
    assert out1['primary_outcome'] == out2['primary_outcome']


def test_repeatability_across_runs():
    items = _sample_items()
    evs = _sample_events()
    out_a = derive_primary_outcome({'items': items}, evs)
    out_b = derive_primary_outcome({'items': items}, evs)
    assert out_a == out_b


def test_finalize_calls_derive_primary_outcome_once(monkeypatch):
    engine = Engine(schema_path='')

    # create a simple checklist_context stub that returns events
    class StubContext:
        def __init__(self):
            self._events = _sample_events()
            self._recorded = []

        def get_events(self):
            return list(self._events)

        def record_event(self, *args, **kwargs):
            self._recorded.append((args, kwargs))

    engine.checklist_context = StubContext()

    calls = {'count': 0}

    def fake_derive(checklist, events):
        calls['count'] += 1
        # delegate to real implementation
        return derive_primary_outcome(checklist, events)

    with patch('shieldcraft.services.checklist.outcome.derive_primary_outcome', new=fake_derive):
        res = finalize_checklist(engine)

    assert calls['count'] == 1
    # ensure result primary_outcome matches derived value
    assert res['primary_outcome'] is not None
    assert res['checklist']['primary_outcome'] == res['primary_outcome']


def test_finalize_handles_derivation_exception_and_still_emits(monkeypatch):
    engine = Engine(schema_path='')

    class StubContext:
        def __init__(self):
            self._events = _sample_events()
            self._recorded = []

        def get_events(self):
            return list(self._events)

        def record_event(self, *args, **kwargs):
            self._recorded.append((args, kwargs))

    engine.checklist_context = StubContext()

    def bad_derive(checklist, events):
        raise RuntimeError("boom")

    with patch('shieldcraft.services.checklist.outcome.derive_primary_outcome', new=bad_derive):
        res = finalize_checklist(engine)

    # finalize_checklist should still return an emitted result and choose a safe outcome consistent with events
    assert res['emitted'] is True
    # sample events include a REFUSAL; fallback should reflect that
    assert res['primary_outcome'] == 'REFUSAL'
    # ensure a diagnostic event was recorded about the derivation failure
    recorded = engine.checklist_context._recorded
    assert any('G_INTERNAL_DERIVATION_FAILURE' in a[0] for a in recorded)
