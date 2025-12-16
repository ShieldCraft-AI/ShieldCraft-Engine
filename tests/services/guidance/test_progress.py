import os
import shutil

from shieldcraft.services.guidance.progress import load_last_state, persist_last_state, compute_progress_summary


def test_persist_and_load_last_state(tmp_path):
    pid = "testprod"
    pdir = tmp_path / "products" / pid
    # emulate workspace by creating expected path
    os.makedirs(pdir, exist_ok=True)
    # monkeypatch working dir by changing cwd
    cwd = os.getcwd()
    try:
        os.chdir(str(tmp_path))
        persist_last_state(pid, "fp1", "VALID", "pass")
        s = load_last_state(pid)
        assert s is not None
        assert s["fingerprint"] == "fp1"
        assert s["conversion_state"] == "VALID"
        assert s["readiness_status"] == "pass"
    finally:
        os.chdir(cwd)


def test_compute_progress_summary_regression():
    prev = {"fingerprint": "old", "conversion_state": "VALID", "readiness_status": "pass"}
    missing = [{"code": "model_empty", "message": "model empty"}]
    readiness = {"results": {"tests_attached": {"ok": False, "reason": "missing_tests"}}}
    # Provide matching fingerprint to enable regression detection
    ps = compute_progress_summary(prev, "CONVERTIBLE", "fail", missing, readiness, current_fingerprint="old")
    assert ps["delta"] == "regressed"
    # reasons should include both missing code and failing gate
    r = ps["reasons"]
    assert "model_empty" in r
    assert any(item.startswith("tests_attached") for item in r)


def test_compute_progress_summary_no_prior():
    ps = compute_progress_summary(None, "CONVERTIBLE", None, [{"code": "model_empty"}], None)
    assert ps["delta"] == "initial"
    assert "model_empty" in ps["reasons"]


def test_compute_progress_summary_mismatched_fingerprint():
    prev = {"fingerprint": "old", "conversion_state": "VALID", "readiness_status": "pass"}
    # Current fingerprint does not match prior; should be treated as initial
    ps = compute_progress_summary(prev, "CONVERTIBLE", "fail", [], None, current_fingerprint="new")
    assert ps["delta"] == "initial"
    assert ps["previous_state"] is None
