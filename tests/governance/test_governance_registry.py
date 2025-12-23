import os
import json

import pytest


def _tmp_artifact(tmp_path, name, content, writable=False):
    d = tmp_path / "docs"
    d.mkdir(exist_ok=True)
    p = d / name
    p.write_text(content)
    if not writable:
        # Ensure read-only for owner/group/other
        p.chmod(0o444)
    else:
        p.chmod(0o666)
    return str(p)


def test_missing_governance_artifact(tmp_path, monkeypatch):
    # Ensure missing artifact triggers deterministic failure
    import shieldcraft.engine as engmod
    import shieldcraft.services.governance.registry as reg

    # Point registry to tmp docs and then remove one artifact
    monkeypatch.setenv("SHIELDCRAFT_PERSONA_ENABLED", "0")
    monkeypatch.setenv("SHIELDCRAFT_SNAPSHOT_ENABLED", "0")
    tmp = tmp_path
    # Create only two artifacts
    _tmp_artifact(tmp, "decision_log.md", "# decisions\n")
    _tmp_artifact(tmp, "OPERATIONAL_READINESS.md", "# ready\n")
    # Monkeypatch required artifacts to point to tmp docs
    monkeypatch.setattr(reg, "REQUIRED_GOVERNANCE_ARTIFACTS", {
        "decision_log": "docs/decision_log.md",
        "operational_readiness": "docs/OPERATIONAL_READINESS.md",
        "contracts": "docs/CONTRACTS.md",
    })
    # Copy a spec into tmp to mark it as a repo root for governance checks
    spec_obj = json.load(open("spec/se_dsl_v1.spec.json"))
    sdir = tmp / "spec"
    sdir.mkdir(exist_ok=True)
    (sdir / "se_dsl_v1.spec.json").write_text(json.dumps(spec_obj))
    # Load spec before changing cwd
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    # Change cwd to tmp so registry checks the temporary artifacts
    monkeypatch.chdir(tmp)
    # Run preflight and expect missing contracts error
    engine = engmod.Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    with pytest.raises(RuntimeError) as e:
        engine.preflight(spec)
    assert "governance_artifact_missing" in str(e.value)


def test_writable_governance_artifact(tmp_path, monkeypatch):
    import shieldcraft.engine as engmod
    import shieldcraft.services.governance.registry as reg

    tmp = tmp_path
    _tmp_artifact(tmp, "decision_log.md", "# decisions\n", writable=True)
    _tmp_artifact(tmp, "OPERATIONAL_READINESS.md", "# ready\n")
    _tmp_artifact(tmp, "CONTRACTS.md", "# contracts\n")

    monkeypatch.setattr(reg, "REQUIRED_GOVERNANCE_ARTIFACTS", {
        "decision_log": "docs/decision_log.md",
        "operational_readiness": "docs/OPERATIONAL_READINESS.md",
        "contracts": "docs/CONTRACTS.md",
    })
    # Use in-repo spec object to avoid depending on cwd
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    # Make tmp look like a repo root for governance checks
    sdir = tmp / "spec"
    sdir.mkdir(exist_ok=True)
    (sdir / "se_dsl_v1.spec.json").write_text(json.dumps(json.load(open("spec/se_dsl_v1.spec.json"))))
    monkeypatch.chdir(tmp)
    engine = engmod.Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    with pytest.raises(RuntimeError) as e:
        engine.preflight(spec)
    assert "governance_artifact_writable" in str(e.value)


def test_version_mismatch(tmp_path, monkeypatch):
    import shieldcraft.engine as engmod
    import shieldcraft.services.governance.registry as reg
    # Create a governance artifact with a mismatched version
    tmp = tmp_path
    _tmp_artifact(tmp, "decision_log.md", "version: 9.0.0\n")
    _tmp_artifact(tmp, "OPERATIONAL_READINESS.md", "# ready\n")
    _tmp_artifact(tmp, "CONTRACTS.md", "# contracts\n")

    monkeypatch.setattr(reg, "REQUIRED_GOVERNANCE_ARTIFACTS", {
        "decision_log": "docs/decision_log.md",
        "operational_readiness": "docs/OPERATIONAL_READINESS.md",
        "contracts": "docs/CONTRACTS.md",
    })
    # Load spec before changing cwd
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    # Make tmp look like a repo root for governance checks
    sdir = tmp / "spec"
    sdir.mkdir(exist_ok=True)
    (sdir / "se_dsl_v1.spec.json").write_text(json.dumps(json.load(open("spec/se_dsl_v1.spec.json"))))
    monkeypatch.chdir(tmp)
    # Ensure the engine reports mismatch (ENGINE_VERSION major is 0 in this repo)
    engine = engmod.Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    with pytest.raises(RuntimeError) as e:
        engine.preflight(spec)
    assert "governance_version_mismatch" in str(e.value)


def test_non_intrusive_enforcement(tmp_path, monkeypatch):
    import shieldcraft.engine as engmod
    import shieldcraft.services.governance.registry as reg

    tmp = tmp_path
    p1 = _tmp_artifact(tmp, "decision_log.md", "version: 0.1.0\nContent\n")
    p2 = _tmp_artifact(tmp, "OPERATIONAL_READINESS.md", "# ready\n")
    p3 = _tmp_artifact(tmp, "CONTRACTS.md", "# contracts\n")
    monkeypatch.setattr(reg, "REQUIRED_GOVERNANCE_ARTIFACTS", {
        "decision_log": "docs/decision_log.md",
        "operational_readiness": "docs/OPERATIONAL_READINESS.md",
        "contracts": "docs/CONTRACTS.md",
    })
    # Load spec before changing cwd
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    monkeypatch.chdir(tmp)
    # Ensure minimal repo sync artifacts so preflight's sync gate passes
    os.makedirs(tmp / "artifacts", exist_ok=True)
    (tmp / "artifacts" / "repo_sync_state.json").write_text('{}')
    import hashlib
    h = hashlib.sha256((tmp / "artifacts" / "repo_sync_state.json").read_bytes()).hexdigest()
    (tmp /
     "repo_state_sync.json").write_text(json.dumps({"files": [{"path": "artifacts/repo_sync_state.json", "sha256": h}]}))
    # Capture mtimes
    mt1 = os.path.getmtime(p1)
    mt2 = os.path.getmtime(p2)
    mt3 = os.path.getmtime(p3)

    engine = engmod.Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    # Should not raise
    engine.preflight(spec)

    # Ensure files unchanged
    assert os.path.getmtime(p1) == mt1
    assert os.path.getmtime(p2) == mt2
    assert os.path.getmtime(p3) == mt3


def test_governance_check_called_in_preflight(monkeypatch):
    import shieldcraft.engine as engmod
    import shieldcraft.services.governance.registry as reg

    # Replace check with a function that raises a recognizable error
    def _boom(root, engine_major=None):
        raise RuntimeError("governance_marker_called")

    monkeypatch.setattr(reg, "check_governance_presence", _boom)
    engine = engmod.Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    with pytest.raises(RuntimeError) as e:
        engine.preflight(spec)
    assert "governance_marker_called" in str(e.value)
