import os
import pytest
from shieldcraft.engine import Engine
from shieldcraft.snapshot import SnapshotError


def test_snapshot_mandatory_mode_requires_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("SHIELDCRAFT_SYNC_AUTHORITY", "snapshot_mandatory")
    # ensure no snapshot present
    monkeypatch.chdir(tmp_path)
    # ensure sync check would not interfere
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_sync", lambda root: {"ok": True})

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    with pytest.raises(SnapshotError):
        engine.preflight({"metadata": {"product_id": "x"}, "model": {"version": "1.0"}, "sections": []})
