from shieldcraft.persona import Persona, PersonaContext
from shieldcraft.persona.persona_registry import register_persona, clear_registry, find_personas_for_phase
from shieldcraft.persona import emit_veto


def test_authority_metadata_does_not_change_veto_semantics(monkeypatch):
    clear_registry()
    p = Persona(name='dec', role=None, scope=['preflight'], allowed_actions=['veto'], constraints={}, authority='DECISIVE')
    register_persona(p)

    class E:
        pass

    engine = E()
    # enable persona feature and monkeypatch repo/worktree checks so emit_veto can run
    monkeypatch.setenv('SHIELDCRAFT_PERSONA_ENABLED', '1')
    import shieldcraft.persona as pm
    monkeypatch.setattr(pm, '_is_worktree_clean', lambda: True)
    # persona context
    ctx = PersonaContext(name='dec', role=None, display_name=None, scope=['preflight'], allowed_actions=['veto'], constraints={}, authority='DECISIVE')
    emit_veto(engine, ctx, 'preflight', 'stop', {'explanation_code': 'x', 'details': 'stop it'}, 'high')
    # enforce_persona_veto should not raise; persona vetoes are advisory
    from shieldcraft.services.validator.persona_gate import enforce_persona_veto
    res = enforce_persona_veto(engine)
    assert res is not None and res.get('persona_id') == 'dec'
