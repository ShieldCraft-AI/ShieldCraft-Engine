import json
import os
import tempfile
import shutil


def test_cli_self_host_success():
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {"metadata": {"product_id": "smoke", "spec_format": "canonical_json_v1", "self_host": True}, "model": {}, "sections": {}}
        json.dump(spec, tmp)
        path = tmp.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        # Ensure sync artifact exists and worktree is considered clean
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
        run_self_host(path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        assert os.path.exists('.selfhost_outputs/manifest.json')
        assert os.path.exists('.selfhost_outputs/summary.json')
    finally:
        os.unlink(path)


def test_cli_self_host_invalid_spec():
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {"metadata": {"product_id": "smoke", "self_host": True}, "invalid": True}
        json.dump(spec, tmp)
        path = tmp.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        # Ensure sync artifact and clean worktree to reach validation stage
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
        run_self_host(path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        # Accept either structured errors.json or generic error.txt
        assert os.path.exists('.selfhost_outputs/errors.json') or os.path.exists('.selfhost_outputs/error.txt')
        assert not os.path.exists('.selfhost_outputs/manifest.json')
    finally:
        os.unlink(path)
