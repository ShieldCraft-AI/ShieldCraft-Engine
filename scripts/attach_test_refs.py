import re
import json
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path('.')
TEST_ROOT = ROOT / 'tests'
CHECKLIST_PATH = Path('artifacts/canonical_full_run/run1/generated_checklist.json')
OUT_DIR = Path('artifacts/test_linkage')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Build test registry
# For each test file, capture: file path, list of test functions, markers, raw content
registry = []
hex_id_re = re.compile(r"[0-9a-f]{10,}")

def extract_tests_from_file(p: Path):
    txt = p.read_text()
    functions = re.findall(r"def\s+(test_[A-Za-z0-9_]+)", txt)
    markers = re.findall(r"@pytest\.mark\.([A-Za-z0-9_]+)", txt)
    # build list of full test ids: file::function
    tests = [f"{str(p)}::{fn}" for fn in functions]
    return {
        'path': str(p),
        'functions': functions,
        'markers': markers,
        'tests_full': tests,
        'content': txt,
    }

for f in sorted(TEST_ROOT.rglob('test_*.py')):
    registry.append(extract_tests_from_file(f))

# Index by signals: id substrings, pointers, file names
id_index = defaultdict(list)  # id -> list of test_full
ptr_index = defaultdict(list)
file_index = defaultdict(list)

for entry in registry:
    content = entry['content']
    # find hex ids in content
    for m in hex_id_re.findall(content):
        id_index[m].extend(entry['tests_full'])
    # find pointer-like strings ("/something") appearing in content
    ptrs = re.findall(r"(/[-A-Za-z0-9_/$]+)", content)
    for p in ptrs:
        ptr_index[p].extend(entry['tests_full'])
    # index by file stem
    stem = Path(entry['path']).stem
    file_index[stem].extend(entry['tests_full'])

# Load checklist
items = json.loads(CHECKLIST_PATH.read_text())

attached = {}
items_with = 0
items_without = 0
unlinked_by_category = Counter()

for it in items:
    itid = it.get('id')
    ptr = it.get('ptr')
    category = it.get('category') or 'unknown'
    matches = set()
    # Direct ID match
    if itid:
        # hex ids may be longer/shorter; match any registry id that contains this substring
        for key, tests in id_index.items():
            if itid in key or key in itid:
                matches.update(tests)
    # direct ptr match
    if ptr:
        if ptr in ptr_index:
            matches.update(ptr_index[ptr])
        # also canonical pointer variations: /$schema -> $schema
        short = ptr.lstrip('/')
        for k, tests in file_index.items():
            if short.startswith(k) or k.startswith(short):
                matches.update(tests)
    # Also search for exact id in any test content (substring scan)
    if itid:
        for entry in registry:
            if itid in entry['content']:
                matches.update(entry['tests_full'])
    # Stabilize ordering
    matches = sorted(set(matches))
    # Rule: attach only when clear direct match exists
    # 'Clear' = at least one test path that contains the exact id or ptr or has function name referencing ptr
    authoritative = []
    for t in matches:
        # inspect file content for exact id or ptr
        fpath, fn = t.split('::')
        content = Path(fpath).read_text()
        if itid and itid in content:
            authoritative.append(t)
        elif ptr and ptr in content:
            authoritative.append(t)
        else:
            # check if fn name contains meaningful words from ptr
            if ptr:
                short = ptr.strip('/').replace('/', '_')
                if short and short in fn:
                    authoritative.append(t)
    authoritative = sorted(set(authoritative))

    if authoritative:
        attached[itid] = authoritative
        items_with += 1
    else:
        attached[itid] = []
        items_without += 1
        unlinked_by_category[category] += 1

# Write report
report = {
    'total_checklist_items': len(items),
    'items_with_test_refs': items_with,
    'items_without_test_refs': items_without,
    'unlinked_by_category': dict(sorted(unlinked_by_category.items())),
    'attached_refs': dict(sorted(attached.items())),
    'gate_report': {
        'gate': 'tests_attached',
        'mode': 'report_only',
        'do_not_halt': True,
        'linked_count': items_with,
        'total_count': len(items),
        'percent_linked': round((items_with / len(items)) * 100, 2) if len(items) else 0.0,
        'blocking_invariants': []
    }
}

OUT = OUT_DIR / 'report.json'
OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
