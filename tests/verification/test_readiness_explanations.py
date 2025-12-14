from shieldcraft.verification.readiness_report import render_readiness


def test_readiness_report_explains_failures():
    report = {
        "ok": False,
        "results": {
            "tests_attached": {"ok": False, "reason": "missing_test_refs"},
            "determinism_replay": {"ok": False, "reason": "mismatch"},
        },
    }
    txt = render_readiness(report)
    assert "NOT READY" in txt
    assert "tests_attached" in txt and "Reason" in txt
