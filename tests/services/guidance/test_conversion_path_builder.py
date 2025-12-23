from shieldcraft.services.guidance.conversion_path import build_conversion_path


def test_conversion_path_structured_from_convertible():
    missing = [{"code": "model_empty", "message": "model is empty"}]
    conv = build_conversion_path("CONVERTIBLE", missing, None)
    assert conv["current_state"] == "CONVERTIBLE"
    assert conv["next_state"] == "STRUCTURED"
    assert len(conv["blocking_requirements"]) >= 1
    assert conv["blocking_requirements"][0]["code"] == "model_empty"
    assert conv["estimated_effort"] in ("low", "medium", "high")


def test_conversion_path_ready_from_valid_reads_readiness():
    readiness = {
        "results": {
            "tests_attached": {
                "ok": False,
                "blocking": True},
            "determinism_replay": {
                "ok": True,
                "blocking": True}}}
    conv = build_conversion_path("VALID", [], readiness)
    assert conv["current_state"] == "VALID"
    assert conv["next_state"] == "READY"
    # Only blocking failing gates should appear
    codes = [b["code"] for b in conv["blocking_requirements"]]
    assert "tests_attached" in codes


def test_conversion_path_never_empty_for_non_ready():
    conv = build_conversion_path("CONVERTIBLE", [], None)
    assert conv["blocking_requirements"], "conversion_path must not be empty"


def test_conversion_path_monotonic_shrink():
    missing1 = [{"code": "model_empty"}, {"code": "invariants_empty"}]
    missing2 = [{"code": "model_empty"}]
    c1 = build_conversion_path("STRUCTURED", missing1, None)
    c2 = build_conversion_path("STRUCTURED", missing2, None)
    assert len(c2["blocking_requirements"]) <= len(c1["blocking_requirements"])


def test_conversion_path_no_schema_changes_suggested():
    conv = build_conversion_path("CONVERTIBLE", [{"code": "sections_empty"}], None)
    for b in conv["blocking_requirements"]:
        s = b.get("suggestion", "").lower()
        assert "schema" not in s and "modify schema" not in s and "change schema" not in s
