from shieldcraft.services.spec.normalization import build_minimal_dsl_skeleton


def test_build_minimal_dsl_skeleton_includes_required_keys():
    raw = "some text"
    s = build_minimal_dsl_skeleton(raw, source_format="yaml")
    assert isinstance(s, dict)
    assert "metadata" in s and "model" in s and "sections" in s
    md = s["metadata"]
    assert md["product_id"] == "unknown"
    assert md["spec_format"] == "canonical_json_v1"
    assert md["normalized"] is True
    assert md["source_material"] == raw


def test_build_minimal_dsl_skeleton_preserves_structured_raw():
    raw = {"a": 1}
    s = build_minimal_dsl_skeleton(raw, source_format="json")
    assert s["metadata"]["source_material"] == raw


def test_ingest_spec_produces_dsl_shape_for_text(tmp_path):
    from shieldcraft.services.spec.ingestion import ingest_spec
    p = tmp_path / "t.yml"
    p.write_text("plain text content")
    spec = ingest_spec(str(p))
    assert isinstance(spec, dict)
    assert "metadata" in spec
    assert spec["metadata"].get("normalized") is True
    assert "model" in spec and "sections" in spec
