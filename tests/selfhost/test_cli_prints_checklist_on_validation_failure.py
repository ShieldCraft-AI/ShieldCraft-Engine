import os
import shutil


def _prepare_env():
    os.makedirs('artifacts', exist_ok=True)
    open('artifacts/repo_sync_state.json', 'w').write('{}')
    import hashlib
    h = hashlib.sha256(open('artifacts/repo_sync_state.json','rb').read()).hexdigest()
    with open('repo_state_sync.json', 'w') as f:
        import json
        json.dump({"files":[{"path":"artifacts/repo_sync_state.json","sha256":h}]}, f)
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)


def test_cli_prints_checklist_on_validation_failure(tmp_path, capsys):
    from shieldcraft.main import run_self_host
    _prepare_env()
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')
    p = tmp_path / "bad.txt"
    p.write_text("this will not parse as a DSL and should trigger validation failure", encoding='utf8')
    run_self_host(str(p), 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    captured = capsys.readouterr()
    assert 'Checklist generated:' in captured.out