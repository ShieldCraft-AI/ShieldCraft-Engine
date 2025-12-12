from shieldcraft.services.checklist.generator import ChecklistGenerator


def test_checklist():
    generator = ChecklistGenerator()
    items = generator.generate([{"type": "section", "ptr": "/x"}])
    # Stable IDs are now 8-char hashes
    assert len(items[0]["id"]) == 8
    assert "ptr" in items[0]
