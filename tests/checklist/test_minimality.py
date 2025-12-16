import json
import os
from shieldcraft.checklist.equivalence import detect_and_collapse


def _req(id='r1'):
    return {'id': id, 'dimensions': ['behavior']}


def _item(iid, claim, reqs, priority='P2', dims=None, confidence=''):
    return {
        'id': iid,
        'claim': claim,
        'requirement_refs': reqs,
        'priority': priority,
        'covers_dimensions': dims or ['behavior'],
        'confidence': confidence,
        'evidence': {'quote': claim}
    }


def test_group_and_collapse_simple():
    reqs = [_req('r1')]
    a = _item('a', 'do x', ['r1'], priority='P1')
    b = _item('b', 'do x', ['r1'], priority='P2')
    items = [a, b]
    pruned, report = detect_and_collapse(items, reqs, outdir='.selfhost_outputs')
    assert report['removed_count'] == 1
    assert any(g['primary'] == 'a' for g in report['equivalence_groups'])
    # primary should have collapsed_from recorded
    prim = next((it for it in pruned if it['id'] == 'a'), None)
    assert prim is not None and prim.get('collapsed_from') == ['b']
    # proof should indicate primary is necessary (removing it reduces completeness)
    assert any(p['primary'] == 'a' and p['necessary'] for p in report['proof_of_minimality'])


def test_detect_violation_when_other_item_covers():
    # Another item outside equivalence group also covers the requirement,
    # making the primary unnecessary once redundant items are collapsed.
    reqs = [_req('r1')]
    a = _item('a', 'do x', ['r1'], priority='P1')
    b = _item('b', 'do x', ['r1'], priority='P2')
    # c covers the same requirement but is not equivalent (different artifact signature)
    c = _item('c', 'ensure y', ['r1'], priority='P2')
    items = [a, b, c]
    pruned, report = detect_and_collapse(items, reqs, outdir='.selfhost_outputs')
    assert report['removed_count'] == 1
    # proof should show a primary that is NOT necessary because c still covers the req
    assert any(not p['necessary'] for p in report['proof_of_minimality'])


def test_deterministic_across_runs(tmp_path):
    reqs = [_req('r1')]
    a = _item('a', 'do x', ['r1'], priority='P1')
    b = _item('b', 'do x', ['r1'], priority='P2')
    items = [a, b]
    p1, r1 = detect_and_collapse(items, reqs, outdir=str(tmp_path))
    p2, r2 = detect_and_collapse(items, reqs, outdir=str(tmp_path))
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


def test_engine_raises_on_minimality_violation(monkeypatch):
    # Monkeypatch detect_and_collapse to simulate a violation
    def fake_detect(items, reqs, outdir='.selfhost_outputs'):
        # keep items unchanged but report a violation
        pruned = items
        report = {'removed_count': 1, 'equivalence_groups': [{'primary': 'a', 'collapsed_from': ['b']}], 'proof_of_minimality': [{'primary': 'a', 'necessary': False, 'delta_complete_pct': 0.0}]}
        return pruned, report

    monkeypatch.setattr('shieldcraft.checklist.equivalence.detect_and_collapse', fake_detect)

    from shieldcraft.engine import Engine
    eng = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')
    # Stub worktree clean check to avoid environment failures
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)
    import pytest
    from shieldcraft.services.spec.ingestion import ingest_spec
    spec = ingest_spec('spec/se_dsl_v1.spec.json')
    # If minimality processing surfaces a fatal condition, ensure it propagates
    def raising_detect(items, reqs, outdir='.selfhost_outputs'):
        raise RuntimeError('minimality_invariant_failed')

    monkeypatch.setattr('shieldcraft.checklist.equivalence.detect_and_collapse', raising_detect)
    import pytest
    with pytest.raises(RuntimeError):
        eng.run_self_host(spec, dry_run=False)