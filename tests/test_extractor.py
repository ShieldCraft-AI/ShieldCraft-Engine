from shieldcraft.services.checklist.extractor import SpecExtractor


def test_recursive_extraction():
    spec = {"a": {"b": 1}, "c": [2, 3]}
    ex = SpecExtractor()
    items = ex.extract(spec)
    ptrs = {i["ptr"] for i in items}
    assert "/a" in ptrs
    assert "/a/b" in ptrs
    assert "/c/0" in ptrs
    assert "/c/1" in ptrs
