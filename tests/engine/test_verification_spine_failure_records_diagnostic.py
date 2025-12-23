from shieldcraft.engine import Engine


def test_verification_spine_failure_records_G6_and_does_not_raise(monkeypatch, tmp_path):
    engine = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')

    # Monkeypatch verification assert to raise
    def fake_assert(props):
        raise RuntimeError('bad properties')
    monkeypatch.setattr('shieldcraft.verification.assertions.assert_verification_properties', fake_assert)

    # Prepare a minimal valid spec file
    sp = tmp_path / 'spec.json'
    sp.write_text(
        '{"metadata": {"product_id": "x", "spec_format": "canonical_json_v1", "self_host": true}, "model": {}, "sections": []}')

    # Call preflight directly so we exercise the verification spine without schema loading
    engine.preflight({"metadata": {"product_id": "x", "spec_format": "canonical_json_v1",
                     "self_host": True}, "model": {}, "sections": []})
    evs = engine.checklist_context.get_events()
    assert any(ev.get('gate_id') == 'G6_VERIFICATION_SPINE_FAILURE' for ev in evs)
