from shieldcraft.services.stability.stability import compare


def test_compare_identical_runs():
    run1 = {
        "signature": "abc123",
        "manifest": {"data": "test"}
    }
    run2 = {
        "signature": "abc123",
        "manifest": {"data": "test"}
    }

    assert compare(run1, run2) is True


def test_compare_different_signatures():
    run1 = {
        "signature": "abc123",
        "manifest": {"data": "test"}
    }
    run2 = {
        "signature": "def456",
        "manifest": {"data": "test"}
    }

    assert compare(run1, run2) is False


def test_compare_no_signatures():
    run1 = {
        "manifest": {"data": "test", "version": "1.0"}
    }
    run2 = {
        "manifest": {"data": "test", "version": "1.0"}
    }

    # Should fallback to deep comparison
    result = compare(run1, run2)
    assert result is True


def test_compare_different_manifests():
    run1 = {
        "manifest": {"data": "test1"}
    }
    run2 = {
        "manifest": {"data": "test2"}
    }

    assert compare(run1, run2) is False


def test_compare_deterministic():
    run1 = {
        "signature": "stable123",
        "manifest": {"field_a": "val1", "field_b": "val2"}
    }
    run2 = {
        "signature": "stable123",
        "manifest": {"field_b": "val2", "field_a": "val1"}  # Different order
    }

    # Should be stable due to signature match
    assert compare(run1, run2) is True


def test_compare_empty_runs():
    run1 = {}
    run2 = {}

    result = compare(run1, run2)
    assert result is True
