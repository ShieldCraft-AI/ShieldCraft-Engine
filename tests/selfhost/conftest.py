import pytest


@pytest.fixture(autouse=True)
def allow_dirty_worktree(monkeypatch):
    """Allow tests in this directory to bypass worktree cleanliness check for isolation."""
    monkeypatch.setenv('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', '1')
    yield
