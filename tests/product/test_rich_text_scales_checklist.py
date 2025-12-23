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


def test_rich_text_scales_checklist():
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    cj = '.selfhost_outputs/checklist.json'
    assert os.path.exists(cj), 'checklist.json missing'
    cl = json.load(open(cj, encoding='utf-8'))
    items = cl.get('items') or []
    assert len(items) >= 50
    # Ensure presence of domain-significant items
    text_blob = "\n".join([(it.get('claim') or it.get('text') or '') for it in items])
    assert 'determin' in text_blob.lower()  # determinism
    assert 'refus' in text_blob.lower() or 'refuse' in text_blob.lower()
    assert 'safe' in text_blob.lower() or 'safe-to-change' in text_blob.lower()
