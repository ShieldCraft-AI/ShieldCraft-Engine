from shieldcraft.persona.persona_registry import register_persona, clear_registry, find_personas_for_phase
from shieldcraft.persona import Persona
from shieldcraft.persona import routing


def test_routing_table_filters_personas():
    clear_registry()
    p1 = Persona(
        name='a',
        role=None,
        scope=['checklist'],
        allowed_actions=['annotate'],
        constraints={},
        authority='ANNOTATIVE')
    p2 = Persona(
        name='b',
        role=None,
        scope=['checklist'],
        allowed_actions=['annotate'],
        constraints={},
        authority='ANNOTATIVE')
    register_persona(p1)
    register_persona(p2)
    # No routing configured -> both personas apply
    res = find_personas_for_phase('checklist')
    assert set([p.name for p in res]) == {'a', 'b'}

    # Configure routing to only include 'b'
    routing.set_routing({'checklist': ['b']})
    res2 = find_personas_for_phase('checklist')
    assert set([p.name for p in res2]) == {'b'}

    # Reset routing
    routing.set_routing({})
    res3 = find_personas_for_phase('checklist')
    assert set([p.name for p in res3]) == {'a', 'b'}
