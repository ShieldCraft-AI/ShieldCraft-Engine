import os
from collections import defaultdict

def test_no_duplicate_test_basenames():
    root = os.path.dirname(os.path.dirname(__file__))
    mapping = defaultdict(list)
    for dirpath, dirnames, filenames in os.walk(os.path.join(root, 'tests')):
        for fn in filenames:
            if fn.startswith('test_') and fn.endswith('.py'):
                mapping[fn].append(os.path.join(dirpath, fn))
    duplicates = {k: v for k, v in mapping.items() if len(v) > 1}
    assert not duplicates, f"Duplicate test basenames detected: {duplicates}"
