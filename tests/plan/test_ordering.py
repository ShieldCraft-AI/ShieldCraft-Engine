"""Test execution plan deterministic ordering."""
import json
from shieldcraft.services.plan.execution_plan import from_ast


def test_deterministic_ordering():
    """Test that execution plan produces identical output for same input."""
    # Mock AST
    class MockNode:
        def __init__(self, ptr):
            self.ptr = ptr

    class MockAST:
        def __init__(self, nodes):
            self._nodes = nodes

        def walk(self):
            return self._nodes

    spec = {
        "metadata": {
            "product_id": "test_product",
            "version": "1.0"
        }
    }

    nodes = [
        MockNode("/metadata"),
        MockNode("/metadata/product_id"),
        MockNode("/sections")
    ]

    ast = MockAST(nodes)

    # Build plan twice with same input
    plan1 = from_ast(ast, spec)
    plan2 = from_ast(ast, spec)

    # Serialize to JSON for comparison
    plan1_json = json.dumps(plan1, sort_keys=True)
    plan2_json = json.dumps(plan2, sort_keys=True)

    # Assert identical serialized output
    assert plan1_json == plan2_json, "Plans should be deterministic"

    # Assert steps have correct ordering
    for idx, step in enumerate(plan1["steps"]):
        assert step["order"] == idx, f"Step {step['id']} has incorrect order"

    for idx, step in enumerate(plan2["steps"]):
        assert step["order"] == idx, f"Step {step['id']} has incorrect order"


def test_no_duplicate_step_names():
    """Test that execution plan has no duplicate step names."""
    class MockNode:
        def __init__(self, ptr):
            self.ptr = ptr

    class MockAST:
        def __init__(self, nodes):
            self._nodes = nodes

        def walk(self):
            return self._nodes

    spec = {
        "metadata": {
            "product_id": "test_product",
            "version": "1.0"
        }
    }

    nodes = [MockNode("/test")]
    ast = MockAST(nodes)

    plan = from_ast(ast, spec)

    # Extract step IDs
    step_ids = [step["id"] for step in plan["steps"]]

    # Assert no duplicates
    assert len(step_ids) == len(set(step_ids)), f"Duplicate step IDs found: {step_ids}"


def test_plan_order_stability():
    """Test that plan maintains stable ordering across multiple builds."""
    class MockNode:
        def __init__(self, ptr):
            self.ptr = ptr

    class MockAST:
        def __init__(self, nodes):
            self._nodes = nodes

        def walk(self):
            return self._nodes

    spec = {
        "metadata": {
            "product_id": "test_product",
            "version": "1.0"
        }
    }

    nodes = [MockNode(f"/section{i}") for i in range(5)]
    ast = MockAST(nodes)

    # Build plan multiple times
    plans = [from_ast(ast, spec) for _ in range(3)]

    # All plans should have same phase order
    phase_orders = [plan["phases"] for plan in plans]
    assert all(phases == phase_orders[0] for phases in phase_orders), "Phase order should be stable"

    # All plans should have same step count
    step_counts = [len(plan["steps"]) for plan in plans]
    assert all(count == step_counts[0] for count in step_counts), "Step count should be stable"


def test_self_host_bootstrap_stage():
    """Test that self-host mode includes bootstrap_codegen stage."""
    class MockNode:
        def __init__(self, ptr):
            self.ptr = ptr

    class MockAST:
        def __init__(self, nodes):
            self._nodes = nodes

        def walk(self):
            return self._nodes

    spec_self_host = {
        "metadata": {
            "product_id": "test_product",
            "version": "1.0",
            "self_host": True
        }
    }

    spec_normal = {
        "metadata": {
            "product_id": "test_product",
            "version": "1.0",
            "self_host": False
        }
    }

    nodes = [MockNode("/test")]
    ast = MockAST(nodes)

    plan_self_host = from_ast(ast, spec_self_host)
    plan_normal = from_ast(ast, spec_normal)

    # Self-host should have bootstrap_codegen phase
    assert "bootstrap_codegen" in plan_self_host["phases"]
    assert plan_self_host["self_host"]

    # Normal mode should not have bootstrap_codegen phase
    assert "bootstrap_codegen" not in plan_normal["phases"]
    assert plan_normal["self_host"] == False
