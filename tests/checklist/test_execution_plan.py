from shieldcraft.checklist.execution_graph import build_execution_plan


def _item(iid, deps=None, priority='P2', produces=None, requires_artifacts=None):
    return {
        'id': iid,
        'depends_on': deps or [],
        'priority': priority,
        'produces_artifacts': produces or [],
        'requires_artifacts': requires_artifacts or []
    }


def test_build_plan_simple():
    a = _item('a')
    b = _item('b', deps=['a'])
    c = _item('c', deps=['a'])
    items = [a, b, c]
    plan = build_execution_plan(items, {})
    assert plan['cycles'] == {}
    assert plan['ordered_item_ids'] and set(plan['ordered_item_ids']) == {'a', 'b', 'c'}
    # a should be before b and c
    assert plan['ordered_item_ids'].index('a') < plan['ordered_item_ids'].index('b')


def test_cycle_detection():
    a = _item('a', deps=['c'])
    b = _item('b', deps=['a'])
    c = _item('c', deps=['b'])
    items = [a, b, c]
    plan = build_execution_plan(items, {})
    assert plan['cycles'] != {}


def test_missing_artifact_detection():
    a = _item('a', produces=['foo'])
    b = _item('b', requires_artifacts=['foo'])
    c = _item('c', requires_artifacts=['bar'])
    items = [a, b, c]
    plan = build_execution_plan(items, {})
    # 'bar' is missing
    assert any('bar' in m for m in plan['missing_artifacts'])


def test_priority_violation():
    a = _item('a', priority='P0', deps=['b'])
    b = _item('b', priority='P2')
    items = [a, b]
    plan = build_execution_plan(items, {})
    assert plan['priority_violations']
