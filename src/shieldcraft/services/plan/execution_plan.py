import hashlib
import json


def build_execution_plan(spec):
    """
    Linear deterministic plan:
    - validate metadata
    - validate rules
    - build rule graph
    - detect cycles
    - generate checklist items
    - extract invariants
    - infer derived tasks
    - run invariants
    - emit manifest
    Returns list of steps.
    """
    return [
        "validate_metadata",
        "validate_rules",
        "build_rule_graph",
        "detect_cycles",
        "generate_items",
        "extract_invariants",
        "infer_derived_tasks",
        "run_invariants",
        "emit_manifest"
    ]


def from_ast(ast, spec=None):
    """
    Generate deterministic seven-phase execution plan from AST.
    If spec.self_host == true, inject bootstrap_codegen stage.
    Includes cycle_resolution stage before bootstrap.
    Returns: dict with phases and step IDs.
    """
    # Deterministic phase ordering
    phases = [
        "dsl_validation",
        "ast_construction",
        "schema_contracts",
        "checklist_generation"
    ]

    # Add cycle resolution stage before bootstrap
    phases.append("cycle_resolution")

    # Check for self-host mode
    if spec and spec.get("metadata", {}).get("self_host") is True:
        # Inject bootstrap_codegen stage
        phases.append("bootstrap_codegen")

    # Continue with standard phases
    phases.extend([
        "codegen",
        "artifact_bundling",
        "stability_verification"
    ])

    # Generate deterministic step IDs based on AST hash
    ast_nodes = [node.ptr for node in ast.walk()]
    ast_hash = hashlib.sha256(json.dumps(ast_nodes, sort_keys=True).encode()).hexdigest()[:8]

    steps = []
    for idx, phase in enumerate(phases):
        step_id = f"{phase}_{ast_hash}_{idx:02d}"
        step_entry = {
            "id": step_id,
            "phase": phase,
            "order": idx,
            "status": "pending"
        }

        # Mark cycle resolution stage with routing info
        if phase == "cycle_resolution":
            step_entry["type_filter"] = "resolve-cycle"

        # Mark bootstrap stage with routing info
        if phase == "bootstrap_codegen":
            step_entry["category_filter"] = "bootstrap"

        steps.append(step_entry)

    # Validate plan invariants
    _assert_plan_invariants(steps)

    return {
        "phases": phases,
        "steps": steps,
        "ast_hash": ast_hash,
        "derived_tasks_included": True,  # Track derived tasks
        "self_host": spec.get("metadata", {}).get("self_host", False) if spec else False
    }


def _assert_plan_invariants(steps):
    """
    Assert execution plan invariants.

    Ensures:
    - Deterministic ordering by step index
    - No duplicate step names

    Raises:
        AssertionError: If invariants are violated.
    """
    # Assert deterministic ordering by index
    for idx, step in enumerate(steps):
        expected_order = step.get("order")
        assert expected_order == idx, f"Step {step['id']} has order {expected_order}, expected {idx}"

    # Assert no duplicate step names
    step_ids = [step.get("id") for step in steps]
    assert len(step_ids) == len(set(step_ids)), f"Duplicate step IDs found: {step_ids}"

    # Assert all steps have required fields
    for step in steps:
        assert "id" in step, f"Step missing id: {step}"
        assert "phase" in step, f"Step missing phase: {step}"
        assert "order" in step, f"Step missing order: {step}"


def validate_bootstrap_stage(plan):
    """
    Validate bootstrap stage in execution plan.

    Ensures:
    - bootstrap_codegen appears exactly once
    - no duplicate bootstrap tasks
    - deterministic order

    Returns: (valid: bool, errors: [])
    """
    errors = []

    # Count bootstrap_codegen occurrences
    bootstrap_stages = [step for step in plan.get("steps", []) if step.get("phase") == "bootstrap_codegen"]

    if len(bootstrap_stages) == 0:
        # Not an error if not self-host
        if plan.get("self_host", False):
            errors.append("Bootstrap stage missing in self-host mode")
    elif len(bootstrap_stages) > 1:
        errors.append(f"Bootstrap stage appears {len(bootstrap_stages)} times, expected 1")

    # Check for duplicate bootstrap tasks
    bootstrap_step_ids = [step.get("id") for step in bootstrap_stages]
    if len(bootstrap_step_ids) != len(set(bootstrap_step_ids)):
        errors.append("Duplicate bootstrap task IDs found")

    # Check deterministic order
    # Bootstrap should appear before final codegen
    steps = plan.get("steps", [])
    bootstrap_idx = None
    codegen_idx = None

    for idx, step in enumerate(steps):
        if step.get("phase") == "bootstrap_codegen":
            bootstrap_idx = idx
        elif step.get("phase") == "codegen":
            codegen_idx = idx

    if bootstrap_idx is not None and codegen_idx is not None:
        if bootstrap_idx >= codegen_idx:
            errors.append("Bootstrap stage must appear before codegen stage")

    return len(errors) == 0, errors


def execute_plan_with_reporting(spec, items):
    """
    Execute plan and report invariant failures and derived items.
    """
    from shieldcraft.services.checklist.invariants import extract_invariants
    from shieldcraft.services.checklist.derived import infer_tasks

    invariant_checks = extract_invariants(spec)
    derived_items = []
    for item in items:
        derived_items.extend(infer_tasks(item))

    return {
        "invariant_failures": [i for i in invariant_checks if i.get("severity") == "error"],
        "derived_items": derived_items
    }
