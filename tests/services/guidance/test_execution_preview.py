from shieldcraft.services.guidance.execution_preview import build_execution_preview


def sample_item(cat, artifact_type=None):
    it = {"category": cat}
    if artifact_type:
        it["artifact_type"] = artifact_type
    return it


def test_preview_for_structured():
    items = [sample_item("bootstrap"), sample_item("test")]
    preview = build_execution_preview("STRUCTURED", items, None, None)
    assert preview is not None
    assert preview["hypothetical"] is True
    assert "bootstrap_code" in preview["would_generate"]
    assert "codegen" in preview["would_execute"]


def test_preview_absent_for_convertible():
    preview = build_execution_preview("CONVERTIBLE", [], None, [])
    assert preview is None


def test_preview_risk_from_readiness():
    readiness = {"results": {"tests_attached": {"ok": False, "blocking": True}}}
    preview = build_execution_preview("VALID", [], readiness, [])
    assert preview is not None
    assert preview["risk_level"] == "high"
