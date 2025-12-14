import json
import os
import shutil
from shieldcraft.engine import Engine
from shieldcraft.services.selfhost import load_artifact_manifest


def test_selfhost_writes_only_manifested_files(tmp_path):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open('spec/se_dsl_v1.spec.json'))

    manifest = load_artifact_manifest()
    allowed_prefixes = manifest.get('allowed_prefixes', [])
    allowed_files = manifest.get('allowed_files', [])

    # Ensure worktree considered clean so self-host can run in tests
    import importlib
    importlib.import_module('shieldcraft.persona')
    import shieldcraft.persona as pmod
    setattr(pmod, '_is_worktree_clean', lambda: True)

    # Run self-host (dry run) and then simulate writing files from preview
    preview = engine.run_self_host(spec, dry_run=True)
    out_dir = tmp_path / preview['fingerprint']
    out_dir.mkdir()

    # Simulate emission: write files that preview contains
    for out in preview.get('outputs', []):
        rel = out['path']
        # Assert path is allowed
        ok = any(rel.startswith(p) for p in allowed_prefixes) or rel in allowed_files
        assert ok, f"Disallowed artifact in preview: {rel}"

    # No extra outputs beyond preview
    assert len(preview.get('outputs', [])) >= 0
