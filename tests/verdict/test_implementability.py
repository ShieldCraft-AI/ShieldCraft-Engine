import os
import json
import shutil
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


def test_se_dsl_is_implementable(tmp_path):
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    p = '.selfhost_outputs/implementability_verdict.json'
    assert os.path.exists(p)
    v = json.load(open(p))
    assert v.get('implementable') is True


def test_minimal_spec_not_implementable(tmp_path):
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    p = tmp_path / 'minimal.yml'
    p.write_text('metadata:\n  product_id: minimal\nsections:\n  important: "This thing must be done"\n')
    run_self_host(str(p), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    v = json.load(open('.selfhost_outputs/implementability_verdict.json'))
    assert v.get('implementable') is False


def test_verdict_deterministic(tmp_path):
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    a = open('.selfhost_outputs/implementability_verdict.json','rb').read()
    # run again and compare
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    _prepare_env()
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    b = open('.selfhost_outputs/implementability_verdict.json','rb').read()
    assert a == b
