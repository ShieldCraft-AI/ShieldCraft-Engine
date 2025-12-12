from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_build_generates_items():
    cg = ChecklistGenerator()
    spec = {"x": 1, "y": 2}
    result = cg.build(spec)
    # Extract items from new dict format
    all_items = result["items"]
    ptrs = [i["ptr"] for i in all_items]
    assert "/x" in ptrs
    assert "/y" in ptrs
