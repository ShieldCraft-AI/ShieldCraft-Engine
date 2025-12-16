from shieldcraft.services.guidance.artifact_contract import build_artifact_contract_summary


def test_artifact_contract_summary_structured():
    ac = {"artifacts": [{"id": "tests"}, {"id": "src"}]}
    checklist = [{"artifact_type": "bootstrap_code"}, {"artifact_type": "tests"}]
    exec_preview = {"would_generate": ["bootstrap_code"]}
    summary = build_artifact_contract_summary("STRUCTURED", ac, checklist, exec_preview)
    assert "conditional" in summary and sorted(summary["conditional"]) == sorted(["bootstrap_code", "src", "tests"])
    assert summary["guaranteed"] == []


def test_artifact_contract_summary_ready_guaranteed():
    ac = {"artifacts": [{"id": "src"}, {"id": "evidence_bundle"}]}
    summary = build_artifact_contract_summary("READY", ac, [], None)
    assert summary["guaranteed"] == ["evidence_bundle", "src"]
    assert summary["conditional"] == []


def test_artifact_contract_summary_unavailable_below_structured():
    ac = {"artifacts": [{"id": "tests"}]}
    summary = build_artifact_contract_summary("CONVERTIBLE", ac, [], None)
    assert summary["unavailable"] == ["tests"]
