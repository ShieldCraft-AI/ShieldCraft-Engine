import json
import os
import shutil


def _prepare_env():
    os.makedirs('artifacts', exist_ok=True)
    open('artifacts/repo_sync_state.json', 'w').write('{}')
    import hashlib
    h = hashlib.sha256(open('artifacts/repo_sync_state.json','rb').read()).hexdigest()
    with open('repo_state_sync.json','w') as f:
        json.dump({"files":[{"path":"artifacts/repo_sync_state.json","sha256":h}]}, f)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)


def _check_items(items):
    verbs = {"verify", "ensure", "confirm", "prevent", "reject", "refuse", "avoid", "maintain", "record", "attach", "add", "update", "remove", "delete", "create", "preserve", "lock", "authorize", "test", "run", "execute", "enforce", "log", "audit", "annotate", "synthesize", "generate", "persist", "validate", "confirm", "fix", "resolve", "implement", "design", "build"}
    for it in items:
        action = it.get('action')
        assert isinstance(action, str) and action, f"Missing action on item {it.get('id')}"
        first = action.split()[0].lower()
        assert first in verbs or action.lower().startswith('implement') or action.lower().startswith('verify')
        ev = it.get('evidence') or {}
        assert ev and (ev.get('quote') or ev.get('source_excerpt_hash') or ev.get('source', {}).get('ptr'))
        conf = it.get('confidence')
        assert conf and conf in ('high', 'medium', 'low')
        assert 'blocking' in it and isinstance(it.get('blocking'), bool)


def test_checklist_items_are_actionable():
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    # Check interpreted/raw checklist
    cj = '.selfhost_outputs/checklist.json'
    assert os.path.exists(cj)
    cl = json.load(open(cj))
    items = cl.get('items') or []
    assert items
    _check_items(items)
    # Check draft checklist if present
    cd = '.selfhost_outputs/checklist_draft.json'
    if os.path.exists(cd):
        draft = json.load(open(cd))
        _check_items(draft.get('items') or [])