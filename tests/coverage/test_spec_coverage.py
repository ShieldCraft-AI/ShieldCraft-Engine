import os
import json
import shutil
from pathlib import Path

from shieldcraft.main import run_self_host


def _prepare_env():
    os.makedirs('artifacts', exist_ok=True)
    open('artifacts/repo_sync_state.json', 'w').write('{}')
    import hashlib
    h = hashlib.sha256(open('artifacts/repo_sync_state.json','rb').read()).hexdigest()
    with open('repo_state_sync.json', 'w') as f:
        json.dump({"files":[{"path":"artifacts/repo_sync_state.json","sha256":h}]}, f)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)


def test_litmus_spec_coverage_high(tmp_path):
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    p = Path('.selfhost_outputs') / 'spec_coverage.json'
    assert p.exists(), 'spec_coverage.json missing'
    c = json.loads(p.read_text())
    assert c.get('covered_pct', 0.0) >= 0.98


def test_uncovered_unit_blocks_sufficiency(tmp_path):
    _prepare_env()
    # Create a minimal spec with one explicit MUST requirement that will be uncovered
    specp = tmp_path / 'minimal.yml'
    specp.write_text('metadata:\n  product_id: minimal\nsections:\n  important: "This thing must be done"\n')
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(str(specp), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    suff = json.loads(open('.selfhost_outputs/checklist_sufficiency.json').read())
    assert suff.get('sufficient') is False
    # Ensure spec_coverage lists uncovered units
    cov = json.loads(open('.selfhost_outputs/spec_coverage.json').read())
    assert cov.get('covered_pct', 1.0) < 1.0


def test_spec_coverage_deterministic(tmp_path):
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    a = open('.selfhost_outputs/spec_coverage.json','rb').read()
    # run again and compare
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    _prepare_env()
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    b = open('.selfhost_outputs/spec_coverage.json','rb').read()
    assert a == b
