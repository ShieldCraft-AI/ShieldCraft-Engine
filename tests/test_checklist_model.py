from shieldcraft.services.checklist.model import ChecklistModel


def test_sorting():
    m = ChecklistModel()
    items = [
        {"id": "b", "ptr": "/z", "text": "t"},
        {"id": "a", "ptr": "/a", "text": "t"},
        {"id": "c", "ptr": "/a", "text": "t"}
    ]
    out = m.deterministic_sort(items)
    assert [i["id"] for i in out] == ["a", "c", "b"]
