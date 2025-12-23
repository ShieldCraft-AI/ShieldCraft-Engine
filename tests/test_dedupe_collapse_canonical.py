from shieldcraft.services.checklist.dedupe import dedupe_items
from shieldcraft.services.checklist.collapse import collapse_items
from shieldcraft.services.checklist.canonical import canonical_sort


def test_dedupe():
    items = [
        {"ptr": "/a", "text": "t", "value": 1},
        {"ptr": "/a", "text": "t", "value": 1},
    ]
    out = dedupe_items(items)
    assert len(out) == 1


def test_collapse():
    items = [
        {"ptr": "/a", "text": "validate", "value": 1},
        {"ptr": "/a", "text": "validate runtime", "value": 2},
    ]
    out = collapse_items(items)
    assert len(out) == 1


def test_canonical():
    items = [
        {"ptr": "/b", "text": "x"},
        {"ptr": "/a", "text": "y"},
    ]
    out = canonical_sort(items)
    assert out[0]["ptr"] == "/a"
