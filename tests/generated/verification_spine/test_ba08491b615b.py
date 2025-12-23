import json
from pathlib import Path

SPEC = Path('spec/se_dsl_v1.spec.json')


def test_ba08491b615b():
    spec = json.loads(SPEC.read_text())
    # Assert exact value at /metadata
    parts = '/metadata'.lstrip('/').split('/')
    cur = spec
    for p in parts:
        assert p in cur, f'Pointer /metadata missing in spec'
        cur = cur[p]
    # Assert explicit scalar metadata entries
    assert isinstance(cur.get('generator_version'), str) and cur.get('generator_version') == '1.0.0'
    assert isinstance(cur.get('language'), str) and cur.get('language') == 'python'
    assert isinstance(cur.get('product_id'), str) and cur.get('product_id') == 'shieldcraft_engine'
    assert isinstance(cur.get('spec_version'), str) and cur.get('spec_version') == '1.0'
    assert cur.get('created_at') == '2025-12-12T00:00:00Z'
    assert cur.get('self_host') is True
