import pytest
import os
import sys
import pathlib

# Ensure tests run with src/ on sys.path using project-root-relative resolution
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Prevent writing .pyc files during test runs to avoid bytecode cache conflicts
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")


@pytest.fixture(autouse=True)
def clear_persona_registry():
    # Ensure persona registry does not leak across tests
    from shieldcraft.persona.persona_registry import clear_registry
    try:
        yield
    finally:
        clear_registry()


@pytest.fixture(autouse=True)
def default_external_sync(monkeypatch):
    """Default test environment: prefer legacy external sync unless a test overrides.

    This keeps most tests stable while allowing specific tests to opt into
    'snapshot' or 'compare' modes explicitly via environment variables.
    """
    monkeypatch.setenv("SHIELDCRAFT_SYNC_AUTHORITY", "external")
    monkeypatch.setenv("SHIELDCRAFT_ALLOW_EXTERNAL_SYNC", "1")
    # Ensure worktree cleanliness checks used by persona runtime return True in tests
    import shieldcraft.persona as pmod
    monkeypatch.setattr(pmod, '_is_worktree_clean', lambda: True)
    yield
