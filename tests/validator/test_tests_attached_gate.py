import pytest

from shieldcraft.services.validator.tests_attached_validator import verify_tests_attached, ProductInvariantFailure


def make_item(id_, test_refs=None):
    it = {"id": id_, "ptr": f"/x/{id_}", "text": "x"}
    if test_refs is not None:
        it["test_refs"] = test_refs
    return it


def test_fails_when_missing_test_refs():
    items = [make_item("a"), make_item("b", ["test::a::t"])]
    with pytest.raises(ProductInvariantFailure) as exc:
        verify_tests_attached(items)
    assert "tests_attached" in str(exc.value)


def test_fails_when_test_refs_empty_array():
    items = [make_item("a", []), make_item("b", ["t"])]
    with pytest.raises(ProductInvariantFailure):
        verify_tests_attached(items)


def test_passes_when_all_items_have_test_refs():
    items = [make_item("a", ["t1"]), make_item("b", ["t2", "t3"])]
    # Should not raise
    verify_tests_attached(items)
