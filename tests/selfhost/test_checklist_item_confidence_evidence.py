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


def _load_checklist():
    return json.loads(open('.selfhost_outputs/checklist_draft.json').read())


def test_checklist_items_have_confidence_and_evidence_on_valid_spec():
    from shieldcraft.main import run_self_host
    _prepare_env()
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    spec_path = str(repo_root / "demos" / "valid.json")
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    assert os.path.exists('.selfhost_outputs/checklist_draft.json')
    cd = _load_checklist()
    items = cd.get('items')
    assert isinstance(items, list) and len(items) > 0
    allowed_conf = {'low', 'medium', 'high'}
    allowed_cats = {'safety', 'refusal', 'determinism', 'governance', 'output_contract', 'misc'}
    for it in items:
        assert it.get('confidence') in allowed_conf
        ev = it.get('evidence')
        assert isinstance(ev, dict)
        assert isinstance(ev.get('source', {}).get('ptr'), str)
        # line may be None, but must exist as a key
        assert 'line' in ev.get('source', {})
        assert it.get('intent_category') in allowed_cats


def test_prose_spec_produces_inferred_items_and_low_confidence():
    from shieldcraft.main import run_self_host
    _prepare_env()
    spec_path = 'spec/test_spec.yml'
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    assert os.path.exists('.selfhost_outputs/checklist_draft.json')
    cd = _load_checklist()
    items = cd.get('items')
    assert isinstance(items, list) and len(items) > 0
    # At least one inferred_from_prose and low confidence
    assert any(it.get('inferred_from_prose') is True and it.get('confidence') == 'low' for it in items)
