from shieldcraft.services.checklist.constraints import propagate_constraints
from shieldcraft.services.checklist.semantic import semantic_validations


def test_missing_required_metadata():
    spec = {"metadata": {}}
    out = propagate_constraints(spec)
    ptrs = [i["ptr"] for i in out]
    assert "/metadata/product_id" in ptrs


def test_invalid_product_id():
    spec = {"metadata": {"product_id": "Bad-ID"}}
    out = semantic_validations(spec)
    assert any("product_id" in i["ptr"] for i in out)


def test_duplicate_agent_ids():
    spec = {"agents": [{"id": "a"}, {"id": "a"}]}
    out = semantic_validations(spec)
    assert any("Duplicate agent id" in i["text"] for i in out)
