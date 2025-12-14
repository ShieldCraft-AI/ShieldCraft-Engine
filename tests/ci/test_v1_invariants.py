import pytest
import os


def test_snapshot_authority_is_default(monkeypatch, tmp_path):
    from shieldcraft.services.sync import verify_repo_state_authoritative

    # Unset any explicit authority and ensure repo_state_sync is used by default
    monkeypatch.delenv('SHIELDCRAFT_SYNC_AUTHORITY', raising=False)
    monkeypatch.delenv('SHIELDCRAFT_ALLOW_EXTERNAL_SYNC', raising=False)

    # In a fresh tmp dir with no repo_state_sync artifact, default mode should NOT raise
    assert verify_repo_state_authoritative(str(tmp_path)).get("ok") is True


def test_external_requires_explicit_opt_in(monkeypatch, tmp_path):
    from shieldcraft.services.sync import verify_repo_state_authoritative, SyncError

    monkeypatch.setenv('SHIELDCRAFT_SYNC_AUTHORITY', 'external')
    monkeypatch.delenv('SHIELDCRAFT_ALLOW_EXTERNAL_SYNC', raising=False)

    with pytest.raises(SyncError):
        verify_repo_state_authoritative(str(tmp_path))
