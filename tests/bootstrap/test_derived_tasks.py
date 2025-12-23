from shieldcraft.services.checklist.derived import infer_tasks
from shieldcraft.services.checklist.classify import classify_item


def test_bootstrap_derived_tasks():
    """Test that bootstrap items generate derived tasks."""
    item = {
        "id": "BOOT-001",
        "ptr": "/metadata/spec_loader",
        "source_pointer": "/metadata/spec_loader",
        "source_section": "metadata",
        "category": "bootstrap",
        "type": "spec_loader",
        "text": "Bootstrap spec loader"
    }

    derived = infer_tasks(item)

    # Should generate bootstrap_impl task
    assert len(derived) > 0
    impl_task = derived[0]
    assert impl_task["type"] == "bootstrap_impl"
    assert impl_task["category"] == "bootstrap"


def test_bootstrap_classification():
    """Test that items from bootstrap sections are classified as bootstrap."""
    item = {
        "ptr": "/metadata/product_id",
        "source_section": "metadata"
    }

    category = classify_item(item)

    assert category == "bootstrap"


def test_bootstrap_derived_task_structure():
    """Test structure of bootstrap derived tasks."""
    item = {
        "id": "BOOT-002",
        "ptr": "/model/version",
        "source_pointer": "/model/version",
        "source_section": "model",
        "category": "bootstrap",
        "type": "default"
    }

    derived = infer_tasks(item)

    assert len(derived) > 0
    task = derived[0]

    # Check required fields
    assert "id" in task
    assert "ptr" in task
    assert "text" in task
    assert "type" in task
    assert "category" in task
    assert "source_pointer" in task
    assert "source_section" in task


def test_non_bootstrap_no_derived():
    """Test that non-bootstrap items don't generate bootstrap derived tasks."""
    item = {
        "id": "GEN-001",
        "ptr": "/features/auth",
        "source_pointer": "/features/auth",
        "source_section": "features",
        "category": "features",
        "text": "Auth feature"
    }

    derived = infer_tasks(item)

    # Should not generate bootstrap tasks
    bootstrap_tasks = [d for d in derived if d.get("type") == "bootstrap_impl"]
    assert len(bootstrap_tasks) == 0


def test_bootstrap_sections_classification():
    """Test all bootstrap sections are classified correctly."""
    bootstrap_sections = ["metadata", "model", "sections"]

    for section in bootstrap_sections:
        item = {
            "ptr": f"/{section}/test",
            "source_section": section
        }

        category = classify_item(item)
        assert category == "bootstrap", f"Section {section} not classified as bootstrap"


def test_derived_tasks_deterministic():
    """Test that derived tasks are deterministic."""
    item = {
        "id": "BOOT-003",
        "ptr": "/sections/core",
        "source_pointer": "/sections/core",
        "source_section": "sections",
        "category": "bootstrap",
        "type": "engine_core"
    }

    derived1 = infer_tasks(item)
    derived2 = infer_tasks(item)

    # Should be identical
    assert derived1 == derived2
