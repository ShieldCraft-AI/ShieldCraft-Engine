import json
import os
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


def test_interpretation_produces_many_items_and_refusals():
    _prepare_env()
    spec_path = 'spec/test_spec.yml'
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')

    run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

    cd_path = Path('.selfhost_outputs') / 'checklist_draft.json'
    assert cd_path.exists()
    cd = json.loads(cd_path.read_text())
    items = cd.get('items', [])
    assert isinstance(items, list)
    # Enforce non-empty and meaning-first counts
    assert len(items) >= 25, f"Expected >=25 interpreted/checklist items, got {len(items)}"
    # At least some refusal/no-touch items
    refusal_related = [it for it in items if ('no' in (it.get('text','').lower()) or 'refuse' in it.get('text','').lower() or 'unsafe' in it.get('text','').lower())]
    assert len(refusal_related) >= 5, f"Expected >=5 refusal-related items, got {len(refusal_related)}"
    # Fail build if <10
    assert len(items) >= 10, "Checklist generation produced too few items (<10)"
