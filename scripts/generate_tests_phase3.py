import json
from pathlib import Path

INCLUDE_CATEGORIES = {"meta", "gov", "general"}
MAX_TESTS = 30
CHECKLIST = Path('artifacts/canonical_full_run/run1/generated_checklist.json')
SPEC = Path('spec/se_dsl_v1.spec.json')
SCHEMA = Path('spec/schemas/se_dsl_v1.schema.json')
OUT_TEST_DIR = Path('tests/generated/verification_spine')
OUT_TEST_DIR.mkdir(parents=True, exist_ok=True)
OUT_REPORT_DIR = Path('artifacts/test_generation')
OUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Load data
checklist = json.loads(CHECKLIST.read_text())
spec = json.loads(SPEC.read_text())
schema = json.loads(SCHEMA.read_text())

# Build metadata required fields from schema
metadata_schema = schema.get('properties', {}).get('metadata', {})
metadata_required = set(metadata_schema.get('required', []))
metadata_props = metadata_schema.get('properties', {})

# Determine existing generated tests
existing_tests = {p.stem.replace('test_', '') for p in Path('tests/generated/verification_spine').glob('test_*.py')}

candidates = []
for it in checklist:
    cid = it.get('id')
    if cid in existing_tests:
        continue
    if it.get('category') not in INCLUDE_CATEGORIES:
        continue
    if it.get('test_refs'):
        continue
    ptr = it.get('ptr')
    if not ptr:
        continue
    # Determine explicit invariants
    invariant = None
    # 1) metadata required presence
    if ptr.startswith('/metadata/'):
        key = ptr.split('/')[2]
        if key in metadata_required:
            prop = metadata_props.get(key, {})
            prop_type = prop.get('type')
            invariant = ({'type': 'required_field', 'ptr': ptr, 'field': key, 'value_type': prop_type})
    # 2) explicit expected value in checklist.value
    if invariant is None and 'value' in it and it.get('value') not in (None, [], {}, ''):
        invariant = ({'type': 'exact_value', 'ptr': ptr, 'value': it.get('value')})
    # 3) boolean explicitly expected in text (e.g., 'Implement boolean at /x: True')
    if invariant is None:
        txt = (it.get('text') or '').lower()
        if 'implement boolean' in txt and ':' in it.get('text', ''):
            # parse trailing literal
            parts = it.get('text').split(':')
            if len(parts) > 1:
                lit = parts[1].strip()
                if lit.lower() in ('true', 'false'):
                    invariant = {'type': 'exact_value', 'ptr': ptr, 'value': True if lit.lower() == 'true' else False}
    if invariant:
        candidates.append((cid, it, invariant))

# Limit to MAX_TESTS
candidates = candidates[:MAX_TESTS]

generated = []
for cid, it, inv in candidates:
    safe = cid.replace(':', '_').replace('/', '_')
    test_name = f"test_{safe}"
    test_path = OUT_TEST_DIR / f"{test_name}.py"
    # Build test content depending on invariant type
    if inv['type'] == 'required_field':
        field = inv['field']
        content = f"""import json
from pathlib import Path

SPEC = Path('spec/se_dsl_v1.spec.json')

def test_{safe}():
    spec = json.loads(SPEC.read_text())
    assert 'metadata' in spec, 'Pointer /metadata missing in spec'
    assert '{field}' in spec['metadata'], 'Pointer /metadata/{field} missing in spec'
    val = spec['metadata']['{field}']
    assert val is not None, 'Spec pointer /metadata/{field} must be present'
"""
    elif inv['type'] == 'exact_value':
        val = inv['value']
        # Compute check_lines if needed
        check_lines_code = ""
        if isinstance(val, dict):
            checks = []
            for k, v in val.items():
                if isinstance(v, (str, bool, int, float)):
                    checks.append((k, v))
            check_lines_code = "\n    ".join([
                ("assert '{k}' in cur and cur['{k}'] == {v_repr}, "
                 "'Invariant failed: {ptr}/{k} != {v_repr}'").format(
                    k=k, v_repr=repr(v), ptr=inv['ptr']) for k, v in checks
            ])
        content = """import json
from pathlib import Path

SPEC=Path('spec/se_dsl_v1.spec.json')

def test_{safe}():
    spec=json.loads(SPEC.read_text())
    # Assert exact value at {inv_ptr}
    parts='{inv_ptr}'.lstrip('/').split('/')
    cur=spec
    for p in parts:
        assert p in cur, f'Pointer {inv_ptr} missing in spec'
        cur = cur[p]
        if isinstance(val, dict):
            checks = []
            for k, v in val.items():
                if isinstance(v, (str, bool, int, float)):
                    checks.append((k, v))
            check_lines = "{check_lines_code}"
            {{check_lines}}
        else:
            assert cur == {val_repr}, 'Invariant failed: {inv_ptr} != {val_repr}'
""".format(safe=safe, inv_ptr=inv['ptr'], check_lines_code=check_lines_code, val_repr=repr(val))
    else:
        continue
    test_path.write_text(content)
    generated.append({'id': cid, 'test': str(test_path), 'invariant': inv})

# produce report
report = {
    'tests_generated': len(generated),
    'items_covered': [g['id'] for g in generated],
    'categories_covered': sorted(list({it.get('category') for _, it, _ in candidates})),
    'remaining_unlinked_items': [it.get('id') for it in checklist if (not it.get('test_refs'))],
    'generated_tests': [{'id': g['id'], 'path': g['test'], 'invariant': g['invariant']} for g in generated]
}
OUT = OUT_REPORT_DIR / 'phase3_report.json'
OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
