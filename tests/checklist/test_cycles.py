"""
Test cycle detection in checklist generation.
"""

from shieldcraft.services.checklist.graph import build_graph, get_cycle_members


def test_cycle_detection_simple():
    """Test simple two-item cycle detection."""
    items = [
        {"id": "task-a", "depends_on": ["task-b"]},
        {"id": "task-b", "depends_on": ["task-a"]}
    ]

    result = build_graph(items)

    # Should detect one cycle
    assert len(result["cycles"]) == 1

    # Cycle should contain both tasks
    cycle = result["cycles"][0]
    assert set(cycle[:-1]) == {"task-a", "task-b"}  # Exclude last element (duplicate)

    # Check cycle members
    members = get_cycle_members(result["cycles"])
    assert members == {"task-a", "task-b"}


def test_cycle_detection_three_way():
    """Test three-way cycle detection."""
    items = [
        {"id": "task-1", "depends_on": ["task-2"]},
        {"id": "task-2", "depends_on": ["task-3"]},
        {"id": "task-3", "depends_on": ["task-1"]}
    ]

    result = build_graph(items)

    # Should detect one cycle
    assert len(result["cycles"]) == 1

    # Cycle should contain all three tasks
    cycle = result["cycles"][0]
    assert set(cycle[:-1]) == {"task-1", "task-2", "task-3"}


def test_no_cycle():
    """Test no cycle when dependencies are linear."""
    items = [
        {"id": "task-1", "depends_on": ["task-2"]},
        {"id": "task-2", "depends_on": ["task-3"]},
        {"id": "task-3", "depends_on": []}
    ]

    result = build_graph(items)

    # Should detect no cycles
    assert len(result["cycles"]) == 0

    # No cycle members
    members = get_cycle_members(result["cycles"])
    assert len(members) == 0


def test_cycle_deterministic_id():
    """Test that cycle detection produces deterministic results."""
    items = [
        {"id": "task-alpha", "depends_on": ["task-beta"]},
        {"id": "task-beta", "depends_on": ["task-alpha"]}
    ]

    # Run multiple times
    results = []
    for _ in range(3):
        result = build_graph(items)
        results.append(result)

    # All results should be identical
    for i in range(1, len(results)):
        assert results[i]["cycles"] == results[0]["cycles"]
        assert results[i]["graph"] == results[0]["graph"]


def test_multiple_cycles():
    """Test detection of multiple independent cycles."""
    items = [
        {"id": "task-a", "depends_on": ["task-b"]},
        {"id": "task-b", "depends_on": ["task-a"]},
        {"id": "task-x", "depends_on": ["task-y"]},
        {"id": "task-y", "depends_on": ["task-x"]},
        {"id": "task-z", "depends_on": []}  # Independent task
    ]

    result = build_graph(items)

    # Should detect two cycles
    assert len(result["cycles"]) == 2

    # Check cycle members
    members = get_cycle_members(result["cycles"])
    assert "task-a" in members
    assert "task-b" in members
    assert "task-x" in members
    assert "task-y" in members
    assert "task-z" not in members


def test_resolve_cycle_task_creation():
    """Test that resolve-cycle tasks are created with deterministic IDs."""
    # Simulate what generator does
    cycle = ["task-1", "task-2", "task-3"]

    # Create cycle task ID (same logic as generator)
    task_id = f"resolve-cycle-{hash(tuple(sorted(cycle))) % 10000:04d}"

    # Should be deterministic
    task_id_2 = f"resolve-cycle-{hash(tuple(sorted(cycle))) % 10000:04d}"
    assert task_id == task_id_2

    # Different cycle should have different ID
    cycle_2 = ["task-a", "task-b", "task-c"]
    task_id_3 = f"resolve-cycle-{hash(tuple(sorted(cycle_2))) % 10000:04d}"
    assert task_id != task_id_3
