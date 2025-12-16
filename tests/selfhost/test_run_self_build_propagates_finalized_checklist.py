import os
from shieldcraft.engine import Engine


def test_run_self_build_propagates_finalized_checklist(monkeypatch, tmp_path):
    # Enable self-build
    os.environ['SHIELDCRAFT_SELFBUILD_ENABLED'] = '1'
    engine = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')

    def fake_run_self_host(self, spec, dry_run=False, emit_preview=None):
        # Simulate a finalized checklist result with no output_dir
        return {'checklist': {'items': [], 'emitted': True, 'events': [{'gate_id':'G14_SELFHOST_INTERNAL_ERROR_RETURN'}]}}

    monkeypatch.setattr('shieldcraft.engine.Engine.run_self_host', fake_run_self_host)

    res = engine.run_self_build(dry_run=False)
    # Should propagate the finalized checklist returned by run_self_host unchanged
    assert isinstance(res, dict)
    assert 'checklist' in res
    assert res['checklist'].get('emitted') is True
