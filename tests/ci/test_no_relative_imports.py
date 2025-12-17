import os
import re

def test_no_relative_imports_in_tests():
    root = os.path.dirname(os.path.dirname(__file__))
    pattern = re.compile(r"^\s*(from|import)\s+\.")
    violations = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(root, 'tests')):
        for fn in filenames:
            if fn.endswith('.py'):
                path = os.path.join(dirpath, fn)
                with open(path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, start=1):
                        if pattern.match(line):
                            violations.append((path, i, line.strip()))
    assert not violations, f"Relative imports found in tests: {violations}"
