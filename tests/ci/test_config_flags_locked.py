import re
from pathlib import Path


def _find_shieldcraft_env_flags() -> set:
    root = Path("src")
    flags = set()
    for p in root.rglob("*.py"):
        s = p.read_text()
        for m in re.finditer(r"SHIELDCRAFT_[A-Z0-9_]+", s):
            flags.add(m.group(0))
    return flags


def test_config_flags_are_listed_and_locked():
    flags_used = _find_shieldcraft_env_flags()
    # Authoritative list of allowed env flags used by the system
    allowed = {
        "SHIELDCRAFT_PERSONA_ENABLED",
        "SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY",
        "SHIELDCRAFT_SELFBUILD_ENABLED",
        "SHIELDCRAFT_SELFBUILD_ESTABLISH_BASELINE",
        "SHIELDCRAFT_SNAPSHOT_ENABLED",
        "SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY",
        "SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT",
        "SHIELDCRAFT_BUILD_DEPTH",
        "SHIELDCRAFT_DETERMINISM_BASE",
        "SHIELDCRAFT_ALLOW_EXTERNAL_SYNC",
        "SHIELDCRAFT_SYNC_AUTHORITY",
    }
    # All discovered flags should be in the allowed list (prevents accidental new flags)
    assert flags_used.issubset(allowed), f"New or unlisted config flags found: {flags_used - allowed}"
