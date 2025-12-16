from shieldcraft.interpreter.interpreter import interpret_raw_spec
from shieldcraft.checklist.item_v1 import ChecklistItemV1
import pathlib


def test_interpret_raw_spec_simple_text():
    text = "Ensure backups are taken daily. Must not delete logs."
    items = interpret_raw_spec(text)
    assert isinstance(items, list)
    assert len(items) >= 1
    for it in items:
        assert isinstance(it, ChecklistItemV1)
        assert it.id
        assert it.claim
        assert it.confidence in ("LOW", "MEDIUM", "HIGH")


def test_interpret_raw_spec_never_empty_for_spec_file():
    p = pathlib.Path(__file__).parents[1].parent / "spec" / "test_spec.yml"
    # fallback if layout differs
    if not p.exists():
        p = pathlib.Path("spec/test_spec.yml")
    txt = p.read_text(encoding="utf8")
    items = interpret_raw_spec(txt)
    assert items and len(items) >= 1