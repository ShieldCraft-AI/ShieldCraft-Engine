import os
import json
import shutil


def _cleanup():
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')


def test_cli_writes_snapshot_error(monkeypatch):
    import importlib
    mod = importlib.import_module('shieldcraft.main')
    from shieldcraft.snapshot import SnapshotError

    _cleanup()

    def fake_engine_runner(self, spec, dry_run=False, emit_preview=None):
        raise SnapshotError('snapshot_missing', 'snapshot file missing', {'path': 'artifacts/repo_snapshot.json'})

    monkeypatch.setattr('shieldcraft.engine.Engine.run_self_host', fake_engine_runner)
    # Call wrapper; ensure errors.json created with snapshot code
    try:
        mod.run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    except Exception:
        pass

    p = os.path.join('.selfhost_outputs', 'errors.json')
    assert os.path.exists(p)
    data = json.load(open(p))
    assert data['errors'][0]['code'] == 'snapshot_missing'


def test_cli_writes_sync_error(monkeypatch):
    import importlib
    mod = importlib.import_module('shieldcraft.main')
    from shieldcraft.services.sync import SyncError

    _cleanup()

    def fake_engine_runner(self, spec, dry_run=False, emit_preview=None):
        raise SyncError('sync_missing', 'repo_state_sync.json not found', '/repo_state_sync.json')

    monkeypatch.setattr('shieldcraft.engine.Engine.run_self_host', fake_engine_runner)
    try:
        mod.run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    except Exception:
        pass

    p = os.path.join('.selfhost_outputs', 'errors.json')
    assert os.path.exists(p)
    data = json.load(open(p))
    assert data['errors'][0]['code'] == 'sync_missing'
