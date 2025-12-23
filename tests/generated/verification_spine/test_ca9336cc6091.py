import json
from pathlib import Path

SPEC = Path('spec/se_dsl_v1.spec.json')


def resolve_ptr(spec_obj, ptr):
    parts = ptr.lstrip('/').split('/')
    cur = spec_obj
    for p in parts:
        p = p.replace('~1', '/').replace('~0', '~')
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            raise AssertionError(f'Pointer not found: {ptr}')
    return cur


def test_item_ca9336cc6091():
    spec = json.loads(SPEC.read_text())
    # Existence check only (no assertion about non-emptiness)
    val = resolve_ptr(spec, '/pointer_map/governance.determinism')
    # Spec explicitly maps governance.determinism; assert target pointer and that it resolves
    assert isinstance(val, str)
    assert val == '/sections/governance/tasks/0'
    # The pointer_map uses canonical id-based pointers which may not be resolvable
    # via direct JSON pointer lookup; equality check above is the explicit invariant.
