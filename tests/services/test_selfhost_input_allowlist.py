import pytest


def test_allowlist_accepts_normal_spec_keys():
    from shieldcraft.services.selfhost import is_allowed_selfhost_input
    good = {"metadata": {}, "instructions": []}
    assert is_allowed_selfhost_input(good) is True


def test_allowlist_accepts_normalized_envelope():
    from shieldcraft.services.selfhost import is_allowed_selfhost_input
    envelope = {"metadata": {"normalized": True, "source_format": "yaml"}, "raw_input": "x"}
    assert is_allowed_selfhost_input(envelope) is True


def test_allowlist_rejects_unmarked_envelope():
    from shieldcraft.services.selfhost import is_allowed_selfhost_input
    envelope = {"metadata": {"normalized": False}, "raw_input": "x"}
    assert is_allowed_selfhost_input(envelope) is False
