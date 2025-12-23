import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SRC_DIR = os.path.join(ROOT, 'src')

ALLOWED_FILES = {
    os.path.join('shieldcraft', 'engine.py'),
    os.path.join('shieldcraft', 'services', 'checklist', 'outcome.py'),
}

ASSIGNMENT_RE = re.compile(r"(?:primary_outcome\s*=|\['primary_outcome'\]\s*=|primary_outcome\s*:)")


def test_no_unauthorized_primary_outcome_assignments():
    violations = []
    for dirpath, dirnames, filenames in os.walk(SRC_DIR):
        for fn in filenames:
            if not fn.endswith('.py'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), SRC_DIR)
            if rel in ALLOWED_FILES:
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    txt = fh.read()
            except Exception: # type: ignore
                continue
            if ASSIGNMENT_RE.search(txt):
                violations.append(rel)
    assert not violations, f"Unauthorized primary_outcome assignments found in: {violations}"
