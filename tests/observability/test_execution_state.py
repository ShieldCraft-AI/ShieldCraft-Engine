import json
import os
from shieldcraft.observability import read_state


def _seq(s):
    return [(e.get("phase"), e.get("gate"), e.get("status")) for e in s]


def test_preflight_emits_states_and_idempotent():
    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))

    engine.preflight(spec)
    s1 = read_state()
    engine.preflight(spec)
    s2 = read_state()

    assert s1 == s2

    # Expected: preflight start/end and validation events are present
    seq = _seq(s1)
    assert seq[0] == ("preflight", "preflight", "start")
    assert ("preflight", "validation", "ok") in seq
    assert seq[-1] == ("preflight", "preflight", "ok")


def test_failure_state_terminal(monkeypatch):
    from shieldcraft.engine import Engine
    from shieldcraft.services.validator import ValidationError

    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    # Force validation to fail deterministically
    monkeypatch.setattr(engine, "_validate_spec", lambda spec: (_ for _ in ()).throw(ValidationError(code="bad_invariant", message="bad")))
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    try:
        engine.preflight(spec)
        assert False, "Expected ValidationError"
    except ValidationError:
        pass

    s = read_state()
    assert s[-1]["status"] == "fail"
    assert "bad_invariant" in s[-1]["error_code"]


def test_selfhost_emits_states_and_non_interference(monkeypatch):
    from shieldcraft.engine import Engine
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))
    # Monkeypatch authoritative sync check to succeed to avoid snapshot/missing issues in local test env
    monkeypatch.setattr("shieldcraft.services.sync.verify_repo_state_authoritative", lambda root: {"ok": True, "sha256": "abc"})
    # Ensure worktree is considered clean for this test
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: True)

    # Call self-host dry-run twice and capture previews
    r1 = engine.run_self_host(spec, dry_run=True)
    s1 = read_state()
    r2 = engine.run_self_host(spec, dry_run=True)
    s2 = read_state()

    assert s1 == s2
    # Ensure self_host start and ok present
    seq = [(e.get("phase"), e.get("gate"), e.get("status")) for e in s1]
    assert ("self_host", "self_host", "start") in seq
    assert ("self_host", "self_host", "ok") in seq

    # Ensure previews unaffected (non-intrusive)
    assert r1 == r2


def test_state_artifact_lock():
    # Only the locked filename should exist for execution state artifacts
    artifacts = os.listdir("artifacts")
    matches = [p for p in artifacts if p.startswith("execution_state")]
    assert matches == ["execution_state_v1.json"]
