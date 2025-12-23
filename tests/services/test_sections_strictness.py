import pytest


def test_sections_gate_off_allows_normalized_skeleton(monkeypatch):
    from shieldcraft.services.spec.normalization import build_minimal_dsl_skeleton
    from shieldcraft.engine import Engine

    spec = build_minimal_dsl_skeleton("", source_format="text")

    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    # Explicitly disable default strictness for this permissive test
    monkeypatch.setenv("SEMANTIC_STRICTNESS_DISABLED", "1")
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative",
                        lambda root: {"ok": True, "sha256": "abc"})

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    res = engine.run_self_host(spec, dry_run=True)
    assert isinstance(res, dict)


def test_sections_gate_on_fails_normalized_skeleton(monkeypatch):
    from shieldcraft.services.spec.normalization import build_minimal_dsl_skeleton
    from shieldcraft.engine import Engine
    from shieldcraft.services.validator import ValidationError

    spec = build_minimal_dsl_skeleton("", source_format="text")

    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    monkeypatch.setenv("SEMANTIC_STRICTNESS_LEVEL_1", "1")
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative",
                        lambda root: {"ok": True, "sha256": "abc"})

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    with pytest.raises(ValidationError) as e:
        engine.run_self_host(spec, dry_run=True)
    assert e.value.code == "sections_empty"


def test_cli_integration_flag_writes_errors_json(monkeypatch, tmp_path):
    import pathlib
    from shieldcraft.main import run_self_host

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    monkeypatch.setenv("SEMANTIC_STRICTNESS_LEVEL_1", "1")
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative",
                        lambda root: {"ok": True, "sha256": "abc"})

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    target_spec_dir = tmp_path / "spec"
    target_spec_dir.mkdir()
    (target_spec_dir / "test_spec.yml").write_text(open(repo_root / "spec" / "test_spec.yml").read())

    run_self_host(str(target_spec_dir / "test_spec.yml"), "src/shieldcraft/dsl/schema/se_dsl.schema.json")

    err = tmp_path / ".selfhost_outputs" / "errors.json"
    assert err.exists()
    data = err.read_text()
    assert "sections_empty" in data


def test_summary_includes_policy_on_validation_failure(monkeypatch, tmp_path):
    import pathlib
    from shieldcraft.main import run_self_host

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    monkeypatch.setenv("SEMANTIC_STRICTNESS_LEVEL_1", "1")
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative",
                        lambda root: {"ok": True, "sha256": "abc"})

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    target_spec_dir = tmp_path / "spec"
    target_spec_dir.mkdir()
    (target_spec_dir / "test_spec.yml").write_text(open(repo_root / "spec" / "test_spec.yml").read())

    run_self_host(str(target_spec_dir / "test_spec.yml"), "src/shieldcraft/dsl/schema/se_dsl.schema.json")

    summary = tmp_path / ".selfhost_outputs" / "summary.json"
    assert summary.exists()
    s = summary.read_text()
    assert "semantic_strictness_policy" in s
    assert "active_levels" in s


def test_level2_only_triggers_invariants_error(monkeypatch, tmp_path):
    import pathlib
    from shieldcraft.main import run_self_host

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    # Explicitly disable default Level 1 strictness to test Level 2 only
    monkeypatch.setenv("SEMANTIC_STRICTNESS_DISABLED", "1")
    monkeypatch.setenv("SEMANTIC_STRICTNESS_LEVEL_2", "1")
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative",
                        lambda root: {"ok": True, "sha256": "abc"})

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    target_spec_dir = tmp_path / "spec"
    target_spec_dir.mkdir()
    (target_spec_dir / "test_spec.yml").write_text(open(repo_root / "spec" / "test_spec.yml").read())

    run_self_host(str(target_spec_dir / "test_spec.yml"), "src/shieldcraft/dsl/schema/se_dsl.schema.json")

    err = tmp_path / ".selfhost_outputs" / "errors.json"
    assert err.exists()
    data = err.read_text()
    assert "invariants_empty" in data


def test_default_enforces_sections_by_default(monkeypatch, tmp_path):
    import pathlib
    from shieldcraft.main import run_self_host

    monkeypatch.chdir(tmp_path)
    # Ensure no explicit disable
    monkeypatch.delenv("SEMANTIC_STRICTNESS_DISABLED", raising=False)
    monkeypatch.delenv("SEMANTIC_STRICTNESS_LEVEL_1", raising=False)
    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative",
                        lambda root: {"ok": True, "sha256": "abc"})

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    target_spec_dir = tmp_path / "spec"
    target_spec_dir.mkdir()
    (target_spec_dir / "test_spec.yml").write_text(open(repo_root / "spec" / "test_spec.yml").read())

    # Default behavior should enforce Level 1 and produce a sections_empty error
    run_self_host(str(target_spec_dir / "test_spec.yml"), "src/shieldcraft/dsl/schema/se_dsl.schema.json")
    err = tmp_path / ".selfhost_outputs" / "errors.json"
    assert err.exists()
    assert "sections_empty" in err.read_text()


def test_disable_semantic_strictness_env_allows_skeleton(monkeypatch, tmp_path):
    import pathlib
    from shieldcraft.main import run_self_host

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SEMANTIC_STRICTNESS_DISABLED", "1")
    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative",
                        lambda root: {"ok": True, "sha256": "abc"})

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    target_spec_dir = tmp_path / "spec"
    target_spec_dir.mkdir()
    (target_spec_dir / "test_spec.yml").write_text(open(repo_root / "spec" / "test_spec.yml").read())

    run_self_host(str(target_spec_dir / "test_spec.yml"), "src/shieldcraft/dsl/schema/se_dsl.schema.json")
    # With strictness disabled, we expect success and summary to exist
    summary = tmp_path / ".selfhost_outputs" / "summary.json"
    assert summary.exists()
