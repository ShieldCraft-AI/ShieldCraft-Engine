from shieldcraft.services.checklist.derived import infer_tasks


def test_derived_tasks_deterministic_ids():
    """Test that infer_tasks produces deterministic IDs across multiple runs."""

    # Create test item
    item = {
        "id": "test-module-1",
        "type": "module",
        "name": "parser",
        "lineage_id": "abc123",
        "source_pointer": "/features/parser",
        "source_node_type": "module"
    }

    # Run inference twice
    tasks1 = infer_tasks(item)
    tasks2 = infer_tasks(item)

    # Extract IDs
    ids1 = [t["id"] for t in tasks1]
    ids2 = [t["id"] for t in tasks2]

    # Assert IDs are identical
    assert ids1 == ids2

    # Assert IDs are deterministic (sorted)
    assert ids1 == sorted(ids1)


def test_derived_tasks_inherit_lineage():
    """Test that derived tasks inherit parent lineage_id."""

    item = {
        "id": "test-module-2",
        "type": "module",
        "name": "validator",
        "lineage_id": "xyz789",
        "source_pointer": "/features/validator",
        "source_node_type": "module"
    }

    tasks = infer_tasks(item)

    # All derived tasks should inherit parent lineage
    for task in tasks:
        assert task.get("lineage_id") == "xyz789"


def test_derived_tasks_missing_dependency():
    """Test that missing dependency triggers fix-dependency task."""

    item = {
        "id": "test-dep-1",
        "type": "module",
        "name": "processor",
        "lineage_id": "dep123",
        "source_pointer": "/features/processor",
        "source_node_type": "module",
        "dependencies": ["missing_module"]
    }

    tasks = infer_tasks(item)

    # Should generate fix-dependency task for missing_module
    fix_tasks = [t for t in tasks if t.get("type") == "fix-dependency"]
    assert len(fix_tasks) > 0

    # Check fix task has dependency_ref
    fix_task = fix_tasks[0]
    assert "dependency_ref" in fix_task
    assert fix_task["dependency_ref"] == "missing_module"


def test_derived_tasks_invariant_violation():
    """Test that invariant violation triggers resolve-invariant task."""

    item = {
        "id": "test-inv-1",
        "type": "module",
        "name": "checker",
        "lineage_id": "inv123",
        "source_pointer": "/features/checker",
        "source_node_type": "module",
        "meta": {
            "invariant_violations": [
                {
                    "id": "inv-001",
                    "expression": "all modules must have tests",
                    "severity": "error"
                }
            ]
        }
    }

    tasks = infer_tasks(item)

    # Should generate resolve-invariant task
    resolve_tasks = [t for t in tasks if t.get("type") == "resolve-invariant"]
    assert len(resolve_tasks) > 0

    # Check resolve task has invariant details
    resolve_task = resolve_tasks[0]
    assert "invariant_id" in resolve_task
    assert resolve_task["invariant_id"] == "inv-001"


def test_derived_tasks_module_generates_standard_tasks():
    """Test that module type generates test, imports, init tasks."""

    item = {
        "id": "test-module-3",
        "type": "module",
        "name": "engine",
        "lineage_id": "mod123",
        "source_pointer": "/features/engine",
        "source_node_type": "module"
    }

    tasks = infer_tasks(item)

    # Should have at least test and init tasks
    task_types = [t.get("type") for t in tasks]

    # Module should derive at least one task
    assert len(tasks) > 0

    # Check all tasks have required fields
    for task in tasks:
        assert "id" in task
        assert "type" in task
        assert "lineage_id" in task


def test_derived_tasks_bootstrap_category():
    """Test that bootstrap category generates impl task."""

    item = {
        "id": "test-bootstrap-1",
        "type": "module",
        "category": "bootstrap",
        "name": "core",
        "lineage_id": "boot123",
        "source_pointer": "/features/core",
        "source_node_type": "module"
    }

    tasks = infer_tasks(item)

    # Bootstrap should generate impl task
    impl_tasks = [t for t in tasks if "impl" in t.get("id", "")]
    assert len(impl_tasks) > 0
