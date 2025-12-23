"""
Test cross-section dependency ordering validation.
"""


def test_cross_section_order_validation():
    """Test that cross-section validation catches out-of-order dependencies."""
    from shieldcraft.services.checklist.cross import cross_section_checks

    spec = {"sections": []}

    # Create items with dependency ordering violation
    items = [
        {"id": "item1", "ptr": "/metadata/version", "deps": ["item2"]},
        {"id": "item2", "ptr": "/architecture/modules", "deps": []},
    ]

    result = cross_section_checks(spec, items=items)

    # Should have violations
    assert "violations" in result
    violations = result["violations"]
    assert len(violations) > 0

    # Check violation structure
    violation = violations[0]
    assert violation["type"] == "cross_section_order"
    assert violation["item"] == "item1"
    assert violation["dep"] == "item2"
    assert "reason" in violation


def test_cross_section_order_valid():
    """Test that valid dependency ordering passes validation."""
    from shieldcraft.services.checklist.cross import cross_section_checks

    spec = {"sections": []}

    # Create items with valid dependency ordering
    items = [
        {"id": "item1", "ptr": "/metadata/version", "deps": []},
        {"id": "item2", "ptr": "/architecture/modules", "deps": ["item1"]},
    ]

    result = cross_section_checks(spec, items=items)

    # Should have no violations
    assert "violations" in result
    violations = result["violations"]
    assert len(violations) == 0


def test_cross_section_order_same_section():
    """Test that dependencies within same section are allowed."""
    from shieldcraft.services.checklist.cross import cross_section_checks

    spec = {"sections": []}

    # Create items in same section with dependencies
    items = [
        {"id": "item1", "ptr": "/metadata/version", "deps": []},
        {"id": "item2", "ptr": "/metadata/name", "deps": ["item1"]},
    ]

    result = cross_section_checks(spec, items=items)

    # Should have no violations for same-section deps
    assert "violations" in result
    violations = result["violations"]
    assert len(violations) == 0
