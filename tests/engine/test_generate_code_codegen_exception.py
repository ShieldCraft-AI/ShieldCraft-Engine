from shieldcraft.engine import Engine


def test_generate_code_handles_codegen_exceptions(monkeypatch):
    engine = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')

    # Make engine.run return a normal successful checklist result
    def fake_run(self, spec_path):
        return {"checklist": {"items": []}}

    monkeypatch.setattr('shieldcraft.engine.Engine.run', fake_run)

    # Simulate codegen.run raising
    def fake_codegen_run(checklist, dry_run=False):
        raise RuntimeError('codegen failure')

    monkeypatch.setattr('shieldcraft.services.codegen.generator.CodeGenerator.run', fake_codegen_run)

    res = engine.generate_code('spec/test_spec.yml', dry_run=True)
    assert isinstance(res, dict)
    # It should be a finalized checklist indicating an internal error
    assert 'checklist' in res
    events = res['checklist'].get('events', [])
    assert any(ev.get('gate_id') == 'G22_CODEGEN_INTERNAL_ERROR_RETURN' for ev in events)
