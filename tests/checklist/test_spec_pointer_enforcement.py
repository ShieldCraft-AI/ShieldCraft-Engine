import pytest
from shieldcraft.services.checklist.model import ChecklistModel


def test_normalize_item_requires_spec_pointer():
    model = ChecklistModel()
    item = {"id": "x", "text": "do something"}  # no ptr or spec_pointer
    with pytest.raises(RuntimeError) as exc:
        model.normalize_item(item)
    assert "missing_spec_pointer" in str(exc.value)


def test_normalize_item_accepts_ptr_and_sets_spec_pointer():
    model = ChecklistModel()
    item = {"id": "x", "ptr": "/sections/1", "text": "do something"}
    out = model.normalize_item(item)
    assert out["spec_pointer"] == "/sections/1"
