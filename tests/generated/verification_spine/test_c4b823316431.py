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


def test_item_c4b823316431():
    spec = json.loads(SPEC.read_text())
    # Existence check only (no assertion about non-emptiness)
    val = resolve_ptr(spec, '/metadata/authors')
    assert val is not None
