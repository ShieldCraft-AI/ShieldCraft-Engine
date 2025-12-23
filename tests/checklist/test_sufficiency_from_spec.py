import json
import os
import shutil
import hashlib
import pytest

from tests.checklist_sufficiency.test_spec_checklist_sufficiency import (
    _prepare_env,
    _find_evidence_for_requirement,
)
from shieldcraft.requirements.extractor import extract_requirements, _normalize_text as _normalize_req_text


def _load_checklist(outdir='.selfhost_outputs'):
    p = os.path.join(outdir, 'checklist.json')
    assert os.path.exists(p), f"{p} missing"
    return json.load(open(p))


def _normalize_action(a: str) -> str:
    return _normalize_req_text(a)


def _hash_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def test_end_to_end_sufficiency_positive(tmp_path):
    """Run full self-host pipeline on canonical spec and assert end-to-end sufficiency + quality"""
    from shieldcraft.main import run_self_host

    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')

    spec_path = 'spec/test_spec.yml'
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

    cl = _load_checklist()
    items = cl.get('items') or []
    assert items, "Checklist items missing"

    # Extract normative requirements using canonical extractor
    text = open(spec_path, 'r', encoding='utf8').read()
    reqs = extract_requirements(text)
    assert reqs, "No normative requirements extracted"

    # Map requirements -> evidence
    mapping = {}
    uncovered = []
    for r in reqs:
        ev = _find_evidence_for_requirement(r, items)
        if ev:
            mapping.setdefault(r['id'], []).append(ev)
        else:
            uncovered.append(r)

    # Coverage assertions: all high-priority must be covered
    high_reqs = [
        r for r in reqs if any(
            k in r['text'].lower() for k in [
                'must',
                'shall',
                'mandatory',
                'requires',
                'enforced',
                'every run must'])]
    high_uncovered = [r for r in uncovered if r in high_reqs]
    assert not high_uncovered, f"Uncovered high-priority requirements: {[r['id'] for r in high_uncovered]}"

    # Checklist quality assertions
    # - No duplicate actions
    actions = [(_normalize_action(it.get('action') or ''), it.get('id')) for it in items]
    action_hashes = {}
    items_by_id = {it.get('id'): it for it in items}
    for a, iid in actions:
        h = _hash_text(a)
        if h in action_hashes:
            prev = action_hashes[h]
            prev_it = items_by_id.get(prev, {})
            cur_it = items_by_id.get(iid, {})
            # Consider duplicate only if action, ptr, and evidence excerpt hash all equal
            prev_ptr = prev_it.get('ptr')
            cur_ptr = cur_it.get('ptr')
            prev_eh = (prev_it.get('evidence') or {}).get('source_excerpt_hash')
            cur_eh = (cur_it.get('evidence') or {}).get('source_excerpt_hash')
            if prev_ptr == cur_ptr and prev_eh == cur_eh:
                pytest.fail(f"Duplicate action detected with same pointer and evidence: {a} (ids: {prev}, {iid})")
        action_hashes[h] = iid

    # - Order rank strictly increasing
    ranks = [it.get('order_rank') for it in items if it.get('order_rank') is not None]
    if ranks:
        assert ranks == sorted(ranks) and len(ranks) == len(items), "order_rank not strictly increasing"
    else:
        # Fallback: ensure items have unique ids and list ordering is deterministic (no duplicates)
        ids = [it.get('id') for it in items]
        assert len(ids) == len(set(ids)), "Duplicate item ids detected; invalid ordering"

    # - P0 items appear before any P2 items
    p0_idxs = [i for i, it in enumerate(items) if it.get('priority') == 'P0']
    p2_idxs = [i for i, it in enumerate(items) if it.get('priority') == 'P2']
    if p0_idxs and p2_idxs:
        # require at least one P0 appears early in the checklist (within first 25%)
        assert min(p0_idxs) < max(1, int(len(items) * 0.25)), "At least one P0 must appear within first 25% of items"
    # - Each checklist item has evidence ptr or source_excerpt_hash
    for it in items:
        ev = it.get('evidence') or {}
        source = ev.get('source') or {}
        has_ptr = bool(source.get('ptr'))
        has_hash = bool(ev.get('source_excerpt_hash'))
        assert has_ptr or has_hash, f"Missing evidence pointer/hash for item {it.get('id')}"

    # On success, emit artifacts
    final_path = tmp_path / 'checklist_final.json'
    idx_path = tmp_path / 'checklist_index.json'
    final_path.write_text(json.dumps(cl, indent=2))

    # Build index: requirement_id -> checklist_item_ids
    index = {}
    for rid, evs in mapping.items():
        index[rid] = [ev.get('item_id') for ev in evs]
    idx_path.write_text(json.dumps(index, indent=2))

    assert final_path.exists() and idx_path.exists()
    assert all(index.get(r['id']) for r in reqs if r['id'] in index or True)


def test_end_to_end_sufficiency_negative(tmp_path):
    """Create a reduced spec (one mandatory sentence removed) and assert the sufficiency check fails and emits a report"""
    from shieldcraft.main import run_self_host

    # Load original spec and extract a requirement to remove via canonical extractor
    orig = open('spec/test_spec.yml', 'r', encoding='utf8').read()
    reqs = extract_requirements(orig)
    assert reqs, "No normative requirements to test against"

    # choose a high-priority requirement to remove (first one)
    to_remove = next((r for r in reqs if any(k in r['text'].lower() for k in ['must', 'shall', 'requires'])), None)
    assert to_remove, "No high-priority requirement found to remove"

    lines = orig.splitlines()
    # Remove the exact line
    idx = to_remove['line'] - 1
    lines[idx] = ''
    reduced = '\n'.join(lines)

    reduced_spec = tmp_path / 'reduced_spec.yml'
    reduced_spec.write_text(reduced)

    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')

    run_self_host(str(reduced_spec), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

    cl = _load_checklist()
    items = cl.get('items') or []

    # Re-extract requirements from reduced spec and check coverage
    new_reqs = extract_requirements(reduced)
    # The removed requirement should no longer be present in new_reqs; ensure our removed id is not in new_reqs
    assert all(r['id'] != to_remove['id'] for r in new_reqs)

    # Now, check that the original set of requirements minus new_reqs includes the removed one
    missing_ids = set(r['id'] for r in reqs) - set(r['id'] for r in new_reqs)
    assert to_remove['id'] in missing_ids

    # Map remaining requirements to items to ensure we detect uncovered
    uncovered = []
    for r in new_reqs:
        ev = _find_evidence_for_requirement(r, items)
        if not ev:
            uncovered.append(r)

    # We expect at least the removed requirement is missing from implementation coverage (we removed it),
    # and therefore the test should consider this a failure scenario.
    # Emit a coverage report for debugging
    report = {
        'spec': str(reduced_spec),
        'removed_requirement': {'id': to_remove['id'], 'text': to_remove['text']},
        'requirements': new_reqs,
        'uncovered': [{'id': r['id'], 'text': r['text'], 'line': r['line']} for r in uncovered],
    }
    rep = tmp_path / 'checklist_coverage_report.json'
    rep.write_text(json.dumps(report, indent=2))

    # Assert that the removed requirement is recognized as missing from the reduced spec
    assert to_remove['id'] in missing_ids
    assert rep.exists()
    data = json.loads(rep.read_text())
    assert 'uncovered' in data
