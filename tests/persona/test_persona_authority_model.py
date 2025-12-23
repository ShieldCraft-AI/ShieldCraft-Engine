import json
from shieldcraft.persona import Persona, PersonaContext, load_persona


def test_persona_authority_field_roundtrip(tmp_path):
    p = Persona(
        name='x',
        role=None,
        display_name=None,
        scope=['preflight'],
        allowed_actions=['annotate'],
        constraints={},
        authority='ANNOTATIVE')
    ctx = PersonaContext(
        name=p.name,
        role=p.role,
        display_name=p.display_name,
        scope=p.scope,
        allowed_actions=p.allowed_actions,
        constraints=p.constraints,
        authority=p.authority)
    d = ctx.to_dict()
    assert d.get('authority') == 'ANNOTATIVE'

    # Now write a persona JSON and load via load_persona
    persona_file = tmp_path / 'persona.json'
    persona_file.write_text(json.dumps({'name': 'y', 'version': '1.0',
                            'persona_version': 'v1', 'authority': 'DECISIVE'}))
    # Monkeypatch repo/worktree checks so load_persona can run in test env
    import shieldcraft.services.sync as syncmod
    syncmod.verify_repo_sync = lambda root: None
    import shieldcraft.persona as pm
    pm._is_worktree_clean = lambda: True
    loaded = load_persona(str(persona_file))
    assert loaded.authority == 'DECISIVE'
