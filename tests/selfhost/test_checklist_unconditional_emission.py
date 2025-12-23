import json
import os
import shutil


def _prepare_env():
    os.makedirs('artifacts', exist_ok=True)
    open('artifacts/repo_sync_state.json', 'w').write('{}')
    import hashlib
    h = hashlib.sha256(open('artifacts/repo_sync_state.json', 'rb').read()).hexdigest()
    with open('repo_state_sync.json', 'w') as f:
        json.dump({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}, f)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)


def test_checklist_unconditional_emission_on_test_spec():
    from shieldcraft.main import run_self_host
    _prepare_env()
    spec_path = 'spec/test_spec.yml'
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    assert os.path.exists('.selfhost_outputs/checklist_draft.json')
    cd = json.load(open('.selfhost_outputs/checklist_draft.json'))
    assert isinstance(cd.get('items'), list)
    assert len(cd.get('items')) > 0
