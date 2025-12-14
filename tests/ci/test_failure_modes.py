import json
import os
import shutil
import pytest
from shieldcraft.engine import Engine


def test_sync_failure_halts_and_no_side_effect(monkeypatch, tmp_path):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Monkeypatch verify_repo_sync to raise
    from shieldcraft.services.sync import SyncError
    def fake_sync(repo_root):
        raise SyncError(code="sync_mismatch", message="mismatch")

    import shieldcraft.services.sync as syncmod
    monkeypatch.setattr(syncmod, 'verify_repo_sync', fake_sync)

    with pytest.raises(RuntimeError):
        engine.preflight({})


def test_selfhost_disallows_partial_on_sync_fail(monkeypatch):
    # Patch verify_repo_sync to raise
    from shieldcraft.services.sync import SyncError
    import shieldcraft.services.sync as syncmod
    monkeypatch.setattr(syncmod, 'verify_repo_sync', lambda root: (_ for _ in ()).throw(SyncError(code='sync_mismatch', message='mismatch')))

    # Run self-host wrapper
    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')

    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    err = os.path.join('.selfhost_outputs','errors.json')
    assert os.path.exists(err)
    data = json.load(open(err))
    assert 'errors' in data


def test_validation_failure_no_side_effects(monkeypatch):
    from shieldcraft.services.validator import ValidationError
    import shieldcraft.services.validator as vmod
    monkeypatch.setattr(vmod, 'validate_instruction_block', lambda spec: (_ for _ in ()).throw(ValidationError(code='x', message='bad', location='/')))

    from shieldcraft.main import run_self_host
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')

    run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
    err = os.path.join('.selfhost_outputs','errors.json')
    assert os.path.exists(err)
    entries = [p for p in os.listdir('.selfhost_outputs') if not p.startswith('.')]
    assert set(entries) == {'errors.json'}
