import json
import os
import shutil
from pathlib import Path

from shieldcraft.main import run_self_host


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


def test_se_dsl_is_sufficient(tmp_path):
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    p = Path('.selfhost_outputs') / 'checklist_sufficiency.json'
    assert p.exists(), "sufficiency artifact missing"
    s = json.loads(p.read_text())
    assert s.get('sufficient') is True
    summary = json.loads(open('.selfhost_outputs/summary.json', encoding='utf-8').read())
    assert summary.get('sufficiency_verdict') is True


def test_prose_only_spec_not_sufficient(tmp_path):
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    spec = tmp_path / 'prose_only.yml'
    spec.write_text('metadata:\n  product_id: prose-only\ndescription: "This is an editorial note, not a requirement."')
    run_self_host(str(spec), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    p = Path('.selfhost_outputs') / 'checklist_sufficiency.json'
    assert p.exists()
    s = json.loads(p.read_text())
    assert s.get('sufficient') is False


def test_litmus_spec_becomes_sufficient_after_fix(tmp_path):
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    run_self_host('spec/test_spec.yml', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    p = Path('.selfhost_outputs') / 'checklist_sufficiency.json'
    assert p.exists()
    s = json.loads(p.read_text())
    assert s.get('sufficient') is False

    # Simulate developer fixes by marking completeness as full
    rc_path = Path('.selfhost_outputs') / 'requirement_completeness.json'
    assert rc_path.exists()
    rc = json.loads(rc_path.read_text())
    # Mark all requirements COMPLETE and complete_pct=1.0
    for r in rc.get('requirements', []):
        r['state'] = 'COMPLETE'
        r['missing_dimensions'] = []
    rc['summary']['complete_pct'] = 1.0
    rc_path.write_text(json.dumps(rc, indent=2, sort_keys=True))

    # Re-run evaluator in-process
    from shieldcraft.sufficiency.evaluator import evaluate_from_files
    new = evaluate_from_files('.selfhost_outputs')
    assert new.get('sufficient') is True
