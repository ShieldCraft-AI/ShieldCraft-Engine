import os
import re


def test_no_todos_or_debug_left():
    # Scan src and docs for TODO, DEBUG, or PROVISIONAL markers
    bad = []
    for root in ("src", "docs"):
        for dirpath, _, files in os.walk(root):
            for f in files:
                if not f.endswith(('.py', '.md', '.json')):
                    continue
                p = os.path.join(dirpath, f)
                s = open(p).read()
                if re.search(r"\bTODO\b|DEBUG|PROVISIONAL", s):
                    bad.append(p)
    assert not bad, f"Found TODO/DEBUG/PROVISIONAL markers in: {bad}"
