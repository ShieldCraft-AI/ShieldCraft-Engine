def test_new_explainability_schema_is_stricter():
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / 'docs' / 'governance' / 'INFERENCE_EXPLAINABILITY_CONTRACT.md'
    text = p.read_text()
    assert 'meta.source' in text
    assert 'meta.inference_type' in text
    assert 'justification' in text
