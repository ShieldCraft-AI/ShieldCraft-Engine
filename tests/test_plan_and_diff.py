from shieldcraft.services.plan.execution_plan import build_execution_plan
from shieldcraft.services.diff.canonical_diff import diff


def test_plan_minimal():
    assert isinstance(build_execution_plan({}), list)


def test_diff_basic():
    a = {"x":1}
    b = {"x":2}
    r = diff(a,b)
    assert len(r["changed"]) == 1
