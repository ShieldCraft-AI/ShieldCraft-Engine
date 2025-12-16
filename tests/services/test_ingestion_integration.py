import os
import pytest


def test_ingestion_promotes_and_engine_accepts(tmp_path, monkeypatch):
    from shieldcraft.services.spec.ingestion import ingest_spec
    from shieldcraft.engine import Engine

    repo_root = tmp_path
    # Copy the sample test_spec.yml into tmp_path
    src = os.path.join(os.getcwd(), "spec", "test_spec.yml")
    dst = repo_root / "test_spec.yml"
    dst.write_text(open(src).read())

    # Ingest the spec
    spec = ingest_spec(str(dst))
    assert isinstance(spec, dict)
    assert spec["metadata"].get("normalized") is True

    # Allow dirty worktree and stub sync to proceed
    monkeypatch.setenv("SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY", "1")
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    # For compatibility with default strictness in CI, disable semantic strictness here
    monkeypatch.setenv("SEMANTIC_STRICTNESS_DISABLED", "1")
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative", lambda root: {"ok": True, "sha256": "abc"})

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    # Ensure engine enforces dict-shaped spec (ingestion contract)
    res = engine.run_self_host(spec, dry_run=True)
    assert isinstance(res, dict)
    assert "manifest" in res


def test_engine_asserts_on_non_dict_inputs(monkeypatch):
    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    with pytest.raises(AssertionError):
        engine.run_self_host("not-a-dict", dry_run=True)

    # For run(), simulate loader returning non-dict to confirm assertion
    monkeypatch.setattr("shieldcraft.engine.load_spec", lambda p: "not-a-dict")
    with pytest.raises(AssertionError):
        engine.run("spec/se_dsl_v1.spec.json")
