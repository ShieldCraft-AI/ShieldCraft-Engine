from shieldcraft.services.checklist.deps import extract_dependencies
from shieldcraft.services.checklist.cross import cross_section_checks


def test_dep_edges():
    spec = {
        "metadata": {"product_id": "x", "version": "1.0.0"},
        "architecture": {"version": "1"},
        "agents": [{"id": "a"}]
    }
    e = extract_dependencies(spec)
    assert any("/architecture/version" in p[0] for p in e)


def test_cross_section_missing_arch():
    spec = {"agents": [{}]}
    out = cross_section_checks(spec)
    assert any("/architecture" in i["ptr"] for i in out)
