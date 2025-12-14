import copy
import json
from pathlib import Path
from shieldcraft.persona.persona_evaluator import evaluate_personas
from types import SimpleNamespace

# Minimal persona-like object
class DummyPersona:
    def __init__(self, name, constraints):
        self.name = name
        self.role = 'tester'
        self.display_name = name
        self.scope = ['checklist']
        self.allowed_actions = []
        self.constraints = constraints


def test_persona_evaluator_does_not_mutate_items():
    engine = SimpleNamespace()
    items = [{"id": "i1", "ptr": "/metadata/product_id", "category": "meta", "meta": {}}]
    items_copy = copy.deepcopy(items)
    personas = [DummyPersona('p1', {"constraint": [{"match": {"id": "i1"}, "set": {"severity": "high"}}]})]

    res = evaluate_personas(engine, personas, items, phase='checklist')
    # evaluator should return constraints but not mutate the provided items
    assert isinstance(res, dict)
    assert res.get('constraints')
    assert items == items_copy