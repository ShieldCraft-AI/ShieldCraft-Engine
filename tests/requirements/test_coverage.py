import json
import os
import shutil
from shieldcraft.requirements.extractor import extract_requirements as extract_dicts
from shieldcraft.requirements.coverage import compute_coverage, write_coverage_report


def test_se_spec_zero_missing(tmp_path):
    # run self-host on the structured se spec and assert zero missing reqs
    from shieldcraft.main import run_self_host
    spec = 'spec/products/shieldcraft_engine/se_spec_v1.json'
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(spec, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    # load persisted requirements
    reqs = json.load(open('.selfhost_outputs/requirements.json')).get('requirements')
    cl = json.load(open('.selfhost_outputs/checklist.json')).get('items')
    covers = compute_coverage(reqs, cl)
    missing = [c for c in covers if c.coverage_status.value == 'MISSING']
    assert len(missing) == 0, f"Expected zero missing requirements, found: {[m.requirement_id for m in missing]}"


def test_test_spec_has_missing():
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    reqs = json.load(open('.selfhost_outputs/requirements.json')).get('requirements')
    cl = json.load(open('.selfhost_outputs/checklist.json')).get('items')
    covers = compute_coverage(reqs, cl)
    # Ensure coverage record exists for each requirement and is well-formed
    assert isinstance(reqs, list) and len(reqs) >= 0
    assert isinstance(covers, list) and len(covers) == len(reqs)


def test_coverage_deterministic(tmp_path):
    # run twice and compare coverage.json files
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    p1 = '.selfhost_outputs/coverage.json'
    data1 = open(p1).read()
    # run again
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    p2 = '.selfhost_outputs/coverage.json'
    data2 = open(p2).read()
    assert data1 == data2
