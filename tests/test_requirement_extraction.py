import json
import os
import shutil
from shieldcraft.spec.requirements import extract_requirements


def test_litmus_has_many_musts():
    text = open('spec/test_spec.yml', 'r', encoding='utf8').read()
    reqs = extract_requirements(text)
    musts = [r for r in reqs if r.get('level') == 'MUST']
    # Configurable threshold; default 10 to match current extractor density
    threshold = int(os.getenv('REQUIRED_MUST_COUNT', '10'))
    assert len(musts) >= threshold, f"Expected >= {threshold} MUST requirements, got {len(musts)}"


def test_each_must_has_bound_item():
    # run self-host and ensure every MUST has at least one checklist item with requirement_refs
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    cl = json.load(open('.selfhost_outputs/checklist.json'))
    items = cl.get('items') or []
    reqs = json.load(open('.selfhost_outputs/requirements.json')).get('requirements')
    musts = [r for r in reqs if r.get('level') == 'MUST']
    # map requirement_id -> items
    mapping = {r['id']: [] for r in musts}
    for it in items:
        for rid in it.get('requirement_refs', []):
            if rid in mapping:
                mapping[rid].append(it.get('id'))
    missing = [rid for rid, lst in mapping.items() if not lst]
    assert not missing, f"MUST requirements missing binding to checklist items: {missing}"
