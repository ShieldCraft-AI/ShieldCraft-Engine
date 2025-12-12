from shieldcraft.services.checklist.idgen import stable_id
from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_stable_ids():
    a = stable_id("/x/y", "hello")
    b = stable_id("/x/y", "hello")
    assert a == b


def test_category_assignment():
    cg = ChecklistGenerator()
    spec = {"metadata": {"name": "x"}}
    result = cg.build(spec)
    # Extract items from new dict format
    all_items = result["items"]
    # Find metadata item
    meta_items = [i for i in all_items if "/metadata" in i["ptr"]]
    assert len(meta_items) > 0
    assert meta_items[0]["classification"] == "metadata"
