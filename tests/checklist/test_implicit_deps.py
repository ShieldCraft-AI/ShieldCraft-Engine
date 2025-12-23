"""
Test implicit dependency extraction.
"""

from shieldcraft.services.checklist.implicit_deps import extract_implicit_deps


def test_extract_depends_on():
    """Test extraction of depends_on dependencies."""
    spec = {
        "task1": {
            "name": "Task 1",
            "depends_on": "task0"
        }
    }

    deps = extract_implicit_deps(spec)

    assert len(deps) > 0
    assert any(d["target"] == "task0" for d in deps)


def test_extract_requires_list():
    """Test extraction of requires list."""
    spec = {
        "task1": {
            "name": "Task 1",
            "requires": ["dep1", "dep2"]
        }
    }

    deps = extract_implicit_deps(spec)

    assert len(deps) >= 2
    targets = [d["target"] for d in deps]
    assert "dep1" in targets
    assert "dep2" in targets


def test_extract_text_references():
    """Test extraction of text references."""
    spec = {
        "task1": {
            "description": "See @ref:other_task for details"
        }
    }

    deps = extract_implicit_deps(spec)

    # Should find text reference
    assert any(d["target"] == "other_task" and d["type"] == "text_reference" for d in deps)


def test_deterministic_ordering():
    """Test that extracted deps are in deterministic order."""
    spec = {
        "z_task": {"depends_on": "a_dep"},
        "a_task": {"depends_on": "z_dep"}
    }

    deps1 = extract_implicit_deps(spec)
    deps2 = extract_implicit_deps(spec)

    assert deps1 == deps2
