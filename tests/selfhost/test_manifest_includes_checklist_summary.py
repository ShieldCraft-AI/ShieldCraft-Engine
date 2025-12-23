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


def test_manifest_has_checklist_summary():
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    mf = json.load(open('.selfhost_outputs/manifest.json'))
    assert 'checklist_preview_items' in mf
    assert 'checklist_preview_summary' in mf
    assert isinstance(mf['checklist_preview_summary'], list)
    assert len(mf['checklist_preview_summary']) <= 5
