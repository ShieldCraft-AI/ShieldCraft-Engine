from shieldcraft.verification.test_expander import expand_tests_for_item


def test_expansion_is_deterministic():
    item = {"id": "item1", "ptr": "/sections/1"}
    test_map = {"test::a::t1": "tests/test_a.py::test_t1", "test::b::t2": "tests/test_b.py::test_t2"}
    e1 = expand_tests_for_item(item, test_map)
    e2 = expand_tests_for_item(item, test_map)
    assert e1 == e2
    assert "candidates" in e1
    assert isinstance(e1["candidates"], list)
