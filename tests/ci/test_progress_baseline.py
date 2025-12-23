import json
import os
import tempfile
import shutil


def _prepare_env():
    # Ensure sync artifact exists and worktree looks clean (used by self-host)
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


def test_self_host_first_observation_is_initial():
    from shieldcraft.main import run_self_host

    _prepare_env()

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {
            "metadata": {
                "product_id": "pb_first",
                "spec_format": "canonical_json_v1",
                "self_host": True},
            "model": {
                "a": 1},
            "sections": [
                {}]}
        json.dump(spec, tmp)
        path = tmp.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        run_self_host(path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        s = json.loads(open('.selfhost_outputs/summary.json', encoding='utf-8').read())
        assert 'progress_summary' in s
        assert s['progress_summary']['delta'] == 'initial'
        assert s['progress_summary'].get('previous_state') is None or s.get('previous_state') is None
    finally:
        os.unlink(path)


def test_validation_runs_do_not_produce_false_regressions():
    from shieldcraft.main import run_self_host

    _prepare_env()

    # Use the provided test spec which is expected to be invalid (validation failure)
    spec_path = 'spec/test_spec.yml'

    # Run multiple times and ensure progress_summary is treated as initial each time
    for _ in range(2):
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        run_self_host(spec_path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        s = json.loads(open('.selfhost_outputs/summary.json', encoding='utf-8').read())
        assert 'progress_summary' in s
        assert s['progress_summary']['delta'] == 'initial'
        assert s['progress_summary'].get('previous_state') is None
