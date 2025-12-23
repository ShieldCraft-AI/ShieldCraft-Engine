"""
Test ordering stability and determinism.
"""


def test_ensure_stable_order_deterministic():
    """Test that ensure_stable_order produces deterministic output."""
    from shieldcraft.services.checklist.order import ensure_stable_order

    # Create items in random order
    items = [
        {"id": "item3", "ptr": "/api/endpoint", "category": "core", "severity": "medium", "origin": {}},
        {"id": "item1", "ptr": "/metadata/version", "category": "core", "severity": "high", "origin": {}},
        {"id": "item2", "ptr": "/architecture/modules", "category": "core", "severity": "critical", "origin": {}},
    ]

    # Sort twice and compare
    result1 = ensure_stable_order(items.copy())
    result2 = ensure_stable_order(items.copy())

    # Should produce identical ordering
    assert len(result1) == len(result2)
    for i in range(len(result1)):
        assert result1[i]["id"] == result2[i]["id"]


def test_ensure_stable_order_section_priority():
    """Test that section order is respected."""
    from shieldcraft.services.checklist.order import ensure_stable_order

    items = [
        {"id": "item1", "ptr": "/api/endpoint", "category": "core", "severity": "high", "origin": {}},
        {"id": "item2", "ptr": "/meta/version", "category": "core", "severity": "high", "origin": {}},
    ]

    result = ensure_stable_order(items)

    # meta section should come before api section
    assert result[0]["ptr"].startswith("/meta")
    assert result[1]["ptr"].startswith("/api")


def test_ensure_stable_order_severity_priority():
    """Test that severity ranking is respected within section."""
    from shieldcraft.services.checklist.order import ensure_stable_order

    items = [
        {"id": "item1", "ptr": "/meta/a", "category": "core", "severity": "low", "origin": {}},
        {"id": "item2", "ptr": "/meta/b", "category": "core", "severity": "critical", "origin": {}},
        {"id": "item3", "ptr": "/meta/c", "category": "core", "severity": "high", "origin": {}},
    ]

    result = ensure_stable_order(items)

    # Critical should come before high, high before low
    severities = [item["severity"] for item in result]
    assert severities == ["critical", "high", "low"]


def test_ensure_stable_order_id_tiebreaker():
    """Test that ID is used as final tiebreaker."""
    from shieldcraft.services.checklist.order import ensure_stable_order

    items = [
        {"id": "item_c", "ptr": "/meta/x", "category": "core", "severity": "high", "origin": {}},
        {"id": "item_a", "ptr": "/meta/y", "category": "core", "severity": "high", "origin": {}},
        {"id": "item_b", "ptr": "/meta/z", "category": "core", "severity": "high", "origin": {}},
    ]

    result = ensure_stable_order(items)

    # Should be sorted by ID
    ids = [item["id"] for item in result]
    assert ids == ["item_a", "item_b", "item_c"]
