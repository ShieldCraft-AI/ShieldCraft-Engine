from shieldcraft.health import generate_system_health, read_system_health


def test_system_health_is_deterministic(tmp_path):
    # Generate twice and assert identical contents
    generate_system_health("artifacts/SYSTEM_HEALTH.md")
    first = read_system_health()
    generate_system_health("artifacts/SYSTEM_HEALTH.md")
    second = read_system_health()
    assert first == second
    assert "Persona Subsystem" in first
