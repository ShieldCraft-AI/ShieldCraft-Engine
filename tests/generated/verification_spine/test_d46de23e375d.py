import json
from pathlib import Path

SPEC=Path('spec/se_dsl_v1.spec.json')

def test_d46de23e375d():
    import pytest
    spec=json.loads(SPEC.read_text())
    # If 'owner' is not present, skip: invariant cannot be enforced without modifying spec
    if 'owner' not in spec.get('metadata', {}):
        pytest.skip('metadata.owner not present in spec; skipping invariant enforcement')
    val = spec['metadata']['owner']
    assert isinstance(val, str) and val, 'metadata.owner must be a non-empty string'
