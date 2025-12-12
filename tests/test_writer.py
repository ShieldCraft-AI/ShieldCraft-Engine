from shieldcraft.services.checklist.writer import ChecklistWriter


def test_writer_basic():
    w = ChecklistWriter()
    out = w.render([("meta", [{"id": "123", "text": "Test task"}])])
    assert "## Metadata" in out
    assert "(123)" in out
    assert "Test task" in out
