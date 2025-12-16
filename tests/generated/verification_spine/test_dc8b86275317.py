import json
from pathlib import Path

SPEC=Path('spec/se_dsl_v1.spec.json')

def test_dc8b86275317():
    spec=json.loads(SPEC.read_text())
    # Assert exact value at /pointer_map/governance.evidence_bundle
    parts='/pointer_map/governance.evidence_bundle'.lstrip('/').split('/')
    cur=spec
    for p in parts:
        assert p in cur, f'Pointer /pointer_map/governance.evidence_bundle missing in spec'
        cur = cur[p]
    assert cur == "/sections/governance/tasks/1", 'Invariant failed: /pointer_map/governance.evidence_bundle != "/sections/governance/tasks/1"'
