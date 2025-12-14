import pytest
import os


def test_snapshot_authority_is_default(monkeypatch, tmp_path):
    from shieldcraft.services.sync import verify_repo_state_authoritative
    from shieldcraft.snapshot import SnapshotError

    # Unset any explicit authority and ensure snapshot is used by default
    monkeypatch.delenv('SHIELDCRAFT_SYNC_AUTHORITY', raising=False)
    monkeypatch.delenv('SHIELDCRAFT_ALLOW_EXTERNAL_SYNC', raising=False)

    # In a fresh tmp dir with no snapshot artifact, snapshot mode should raise SnapshotError
    with pytest.raises(SnapshotError):
        verify_repo_state_authoritative(str(tmp_path))


def test_external_requires_explicit_opt_in(monkeypatch, tmp_path):
    from shieldcraft.services.sync import verify_repo_state_authoritative, SyncError

    monkeypatch.setenv('SHIELDCRAFT_SYNC_AUTHORITY', 'external')
    monkeypatch.delenv('SHIELDCRAFT_ALLOW_EXTERNAL_SYNC', raising=False)

    with pytest.raises(SyncError):
        verify_repo_state_authoritative(str(tmp_path))
