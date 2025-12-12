from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_render_basic():
    cg = ChecklistGenerator()
    spec = {"x": 1}
    result = cg.build(spec)
    # Extract items from new dict format
    all_items = result["items"]
    x_item = [i for i in all_items if i["ptr"] == "/x"][0]
    # Updated assertion to match new render_task implementation
    assert x_item["text"].startswith("Implement value")

