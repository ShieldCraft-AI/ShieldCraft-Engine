import os


def test_normalized_empty_skeleton_selfhost_produces_classification(monkeypatch, tmp_path):
    from shieldcraft.services.spec.normalization import build_minimal_dsl_skeleton
    from shieldcraft.engine import Engine

    spec = build_minimal_dsl_skeleton("", source_format="text")

    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    # Disable default strictness for this visibility test so it can complete
    monkeypatch.setenv("SEMANTIC_STRICTNESS_DISABLED", "1")
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative", lambda root: {"ok": True, "sha256": "abc"})

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    res = engine.run_self_host(spec, dry_run=True)
    assert isinstance(res, dict)
    manifest = res.get("manifest", {})
    assert "dsl_section_classification" in manifest
    cls = manifest.get("dsl_section_classification")
    # Basic sanity: metadata/model/sections should be classified
    assert "metadata" in cls and "model" in cls and "sections" in cls


def test_cli_selfhost_writes_summary_with_classification(monkeypatch, tmp_path):
    # Run CLI against sample test_spec.yml allowing dirty worktree and verify summary
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative", lambda root: {"ok": True, "sha256": "abc"})

    os.makedirs(tmp_path / "artifacts", exist_ok=True)
    # Copy spec into repo and run main.run_self_host
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    repo_spec = repo_root / "spec" / "test_spec.yml"
    target_spec_dir = tmp_path / "spec"
    target_spec_dir.mkdir()
    (target_spec_dir / "test_spec.yml").write_text(open(repo_spec).read())

    from shieldcraft.main import run_self_host
    run_self_host(str(target_spec_dir / "test_spec.yml"), "src/shieldcraft/dsl/schema/se_dsl.schema.json")

    # Read summary
    s = tmp_path / ".selfhost_outputs" / "summary.json"
    assert s.exists()
    data = s.read_text()
    assert "dsl_section_classification" in data
