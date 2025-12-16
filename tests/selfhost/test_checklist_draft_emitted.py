import json
import os
import shutil


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


def test_checklist_draft_emitted_on_invalid_spec():
    from shieldcraft.main import run_self_host
    _prepare_env()
    # Use the provided test spec which is expected to be invalid (validation failure)
    spec_path = 'spec/test_spec.yml'
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    assert os.path.exists('.selfhost_outputs/checklist_draft.json')
    cd = json.loads(open('.selfhost_outputs/checklist_draft.json').read())
    assert isinstance(cd.get('items'), list)
    assert len(cd.get('items')) > 0
    # Summary should indicate checklist emission and draft status
    s = json.loads(open('.selfhost_outputs/summary.json').read())
    assert s.get('checklist_emitted') is True
    assert s.get('checklist_status') == 'draft'


def test_checklist_draft_emitted_on_valid_spec():
    from shieldcraft.main import run_self_host
    _prepare_env()
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    spec_path = str(repo_root / "demos" / "valid.json")
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    assert os.path.exists('.selfhost_outputs/checklist_draft.json')
    cd = json.loads(open('.selfhost_outputs/checklist_draft.json').read())
    assert isinstance(cd.get('items'), list)
    s = json.loads(open('.selfhost_outputs/summary.json').read())
    assert s.get('checklist_emitted') is True
    # For a valid spec, status should be 'ok' or 'draft' depending on readiness
    assert s.get('checklist_status') in ('ok', 'draft', None)
