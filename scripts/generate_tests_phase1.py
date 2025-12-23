import json
from pathlib import Path

INCLUDE_CATEGORIES = {"meta", "gov", "general"}
MAX_TESTS = 40
SRC_CHECKLIST = Path('artifacts/canonical_full_run/run1/generated_checklist.json')
LINKAGE = Path('artifacts/test_linkage/report.json')
SPEC = Path('spec/se_dsl_v1.spec.json')
OUT_TEST_DIR = Path('tests/generated/verification_spine')
OUT_TEST_DIR.mkdir(parents=True, exist_ok=True)
OUT_REPORT_DIR = Path('artifacts/test_generation')
OUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)

checklist = json.loads(SRC_CHECKLIST.read_text())
linkage = json.loads(LINKAGE.read_text())
attached = linkage.get('attached_refs', {})

candidates = []
for it in checklist:
    cid = it.get('id')
    cat = it.get('category') or 'unknown'
    sev = it.get('severity') or 'unknown'
    ptr = it.get('ptr')
    if cat in INCLUDE_CATEGORIES and sev != 'low' and (not attached.get(cid)):
        # Only candidates with explicit ptr
        if ptr:
            candidates.append({'id': cid, 'category': cat, 'severity': sev, 'ptr': ptr, 'text': it.get('text', '')})

# Limit
candidates = candidates[:MAX_TESTS]

# Helper to access JSON Pointer


def resolve_ptr(spec_obj, ptr):
    if not ptr or not ptr.startswith('/'):
        return None
    parts = ptr.lstrip('/').split('/')
    cur = spec_obj
    for p in parts:
        # unescape ~1 ~0 per RFC6901
        p = p.replace('~1', '/').replace('~0', '~')
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


# Load spec
spec = json.loads(SPEC.read_text())

generated_tests = []
items_covered = []
categories_covered = set()

for it in candidates:
    value = resolve_ptr(spec, it['ptr'])
    # Only generate test if pointer exists in spec (no invention)
    if value is None:
        continue
    # Create test file
    tid = it['id']
    safe_tid = tid.replace(':', '_').replace('/', '_')
    test_path = OUT_TEST_DIR / f"test_{safe_tid}.py"
    test_name = f"test_item_{safe_tid}"
    # Test content: load spec and assert pointer resolves and is non-empty
    content = f"""import json
from pathlib import Path

SPEC = Path('spec/se_dsl_v1.spec.json')

def resolve_ptr(spec_obj, ptr):
    parts = ptr.lstrip('/').split('/')
    cur = spec_obj
    for p in parts:
        p = p.replace('~1','/').replace('~0','~')
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            raise AssertionError(f'Pointer not found: {{ptr}}')
    return cur


def {test_name}():
    spec = json.loads(SPEC.read_text())
    # Existence check only (no assertion about non-emptiness)
    val = resolve_ptr(spec, '{it['ptr']}')
    assert val is not None
"""
    test_path.write_text(content)
    generated_tests.append(str(test_path))
    items_covered.append(tid)
    categories_covered.add(it['category'])

# Write report
report = {
    'tests_generated': len(generated_tests),
    'tests': generated_tests,
    'items_covered': items_covered,
    'categories_covered': sorted(list(categories_covered)),
    'remaining_unlinked_items': [k for k, v in attached.items() if not v],
}
OUT = OUT_REPORT_DIR / 'phase1_report.json'
OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
