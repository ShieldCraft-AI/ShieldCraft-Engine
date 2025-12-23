from shieldcraft.engine import Engine
import pytest


@pytest.mark.parametrize("gate,patch_target,return_value",
                         [("G16_MINIMALITY_INVARIANT_FAILED",
                           'shieldcraft.checklist.equivalence.detect_and_collapse',
                           ([],
                            {'proof_of_minimality': [{'necessary': False}],
                               'removed_count': 1,
                               'equivalence_groups': []})),
                             ("G17_EXECUTION_CYCLE_DETECTED",
                              'shieldcraft.checklist.execution_graph.build_execution_plan',
                              {'ordered_item_ids': [],
                               'cycles': ['a'],
                               'missing_artifacts': [],
                               'priority_violations': []}),
                             ("G18_MISSING_ARTIFACT_PRODUCER",
                              'shieldcraft.checklist.execution_graph.build_execution_plan',
                              {'ordered_item_ids': [],
                               'cycles': [],
                               'missing_artifacts': ['x'],
                               'priority_violations': []}),
                             ("G19_PRIORITY_VIOLATION_DETECTED",
                              'shieldcraft.checklist.execution_graph.build_execution_plan',
                              {'ordered_item_ids': [],
                               'cycles': [],
                               'missing_artifacts': [],
                               'priority_violations': ['p']}),
                          ])
def test_selfhost_postprocessing_gates_return_checklist(monkeypatch, tmp_path, gate, patch_target, return_value):
    engine = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')

    # Isolate filesystem to avoid writing to repo
    monkeypatch.chdir(tmp_path)

    # Provide a valid spec that reaches post-processing
    spec = {
        "metadata": {"product_id": "test"},
        "instructions": [],
        "invariants": ["some_invariant"],
        "model": {"dependencies": []}
    }

    # Monkeypatch routines to trigger the specific gate
    if 'detect_and_collapse' in patch_target:
        def fake_detect_and_collapse(items, reqs):
            return return_value[0], return_value[1]
        monkeypatch.setattr(patch_target, fake_detect_and_collapse)
    else:
        def fake_build_execution_plan(pruned_items, inferred):
            return return_value
        monkeypatch.setattr(patch_target, fake_build_execution_plan)

    # Run engine self-host (real run, not dry_run) and assert checklist returned with event
    res = engine.run_self_host(spec, dry_run=False)
    assert isinstance(res, dict)
    cl = res.get('checklist', {})
    events = cl.get('events', [])
    assert any(ev.get('gate_id') == gate for ev in events)
