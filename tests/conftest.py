import pytest


@pytest.fixture(autouse=True)
def clear_persona_registry():
    # Ensure persona registry does not leak across tests
    from shieldcraft.persona.persona_registry import clear_registry
    try:
        yield
    finally:
        clear_registry()
import pytest


@pytest.fixture(autouse=True)
def default_external_sync(monkeypatch):
    """Default test environment: prefer legacy external sync unless a test overrides.

    This keeps most tests stable while allowing specific tests to opt into
    'snapshot' or 'compare' modes explicitly via environment variables.
    """
    monkeypatch.setenv("SHIELDCRAFT_SYNC_AUTHORITY", "external")
    monkeypatch.setenv("SHIELDCRAFT_ALLOW_EXTERNAL_SYNC", "1")
    yield
