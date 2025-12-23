import json
from pathlib import Path

SPEC = Path('spec/se_dsl_v1.spec.json')


def test_a40d9cade076():
    spec = json.loads(SPEC.read_text())
    assert 'metadata' in spec, 'Pointer /metadata missing in spec'
    assert 'product_id' in spec['metadata'], 'Pointer /metadata/product_id missing in spec'
    val = spec['metadata']['product_id']
    assert val is not None, 'Spec pointer /metadata/product_id must be present'
