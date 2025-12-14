from shieldcraft.services.validator.test_gate import enforce_tests_attached


def test_invalid_test_ref_is_localized():
    items = [{"id": "i1", "ptr": "/s/1", "test_refs": ["test::missing::t1"]}]
    try:
        enforce_tests_attached(items)
        assert False, "Expected RuntimeError for invalid_test_refs"
    except RuntimeError as e:
        assert "invalid_test_refs" in str(e)
