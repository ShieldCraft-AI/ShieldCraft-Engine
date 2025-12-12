from shieldcraft.services.checklist.sections import ordered_sections


def test_section_order():
    assert ordered_sections(["misc", "meta"]) == ["meta", "misc"]
