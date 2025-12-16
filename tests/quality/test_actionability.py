import os
import json
import shutil
import pytest

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


def test_litmus_checklist_passes_quality(tmp_path):
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    qpath = os.path.join('.selfhost_outputs', 'checklist_quality.json')
    assert os.path.exists(qpath)
    q = json.load(open(qpath))
    summary = q.get('summary', {})
    total = summary.get('total_items', 0)
    low = summary.get('low_signal_count', 0)
    low_ids = summary.get('low_signal_item_ids', [])
    assert total > 0
    assert low / total <= 0.05
    # ensure no P0 in low ids
    items = json.load(open('.selfhost_outputs/checklist.json')).get('items', [])
    id_to_pr = {it.get('id'): it.get('priority') for it in items}
    assert not any((id_to_pr.get(i) or '').upper().startswith('P0') for i in low_ids)


def test_prose_only_spec_fails_quality(tmp_path):
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    spec = tmp_path / 'prose_only.yml'
    spec.write_text('metadata:\n  product_id: prose-only\ndescription: "This is an editorial note, not a requirement."')
    with pytest.raises(RuntimeError):
        run_self_host(str(spec), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    # ensure quality report exists and signals low signal
    qpath = os.path.join('.selfhost_outputs', 'checklist_quality.json')
    assert os.path.exists(qpath)
    q = json.load(open(qpath))
    assert q.get('summary', {}).get('low_signal_count', 0) > 0
