"""Test pointer_map validation."""
import json
from pathlib import Path


def test_pointer_map_unique_keys():
    """Test that pointer_map has unique keys."""
    pointer_map_path = Path(__file__).parent.parent.parent / "spec/pointer_map.json"
    with open(pointer_map_path, encoding='utf-8') as f:
        pointer_map = json.load(f)

    keys = list(pointer_map.keys())

    assert len(keys) == len(set(keys)), "pointer_map has duplicate keys"


def test_pointer_map_all_resolve():
    """Test that all pointers in pointer_map resolve to valid spec locations."""
    pointer_map_path = Path(__file__).parent.parent.parent / "spec/pointer_map.json"
    with open(pointer_map_path, encoding='utf-8') as f:
        pointer_map = json.load(f)

    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    # Simple pointer resolution
    def resolve_pointer(ptr, obj):
        """Resolve JSON Pointer."""
        if not ptr:
            return obj
        if ptr == "/":
            return obj

        parts = ptr.split("/")[1:]  # Skip empty first element
        current = obj

        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    if idx >= len(current):
                        return None
                    current = current[idx]
                except (ValueError, IndexError):
                    return None
            else:
                return None

        return current

    unresolved = []
    for task_id, ptr in pointer_map.items():
        result = resolve_pointer(ptr, spec)
        if result is None:
            unresolved.append(f"{task_id} -> {ptr}")

    assert len(unresolved) == 0, f"Unresolved pointers: {unresolved}"


def test_pointer_map_matches_spec_tasks():
    """Test that pointer_map entries match tasks in spec."""
    pointer_map_path = Path(__file__).parent.parent.parent / "spec/pointer_map.json"
    with open(pointer_map_path, encoding='utf-8') as f:
        pointer_map = json.load(f)

    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    # Collect all task IDs from spec
    task_ids_in_spec = set()
    for section in spec["sections"]:
        for task in section.get("tasks", []):
            task_ids_in_spec.add(task["id"])

    # Check pointer_map keys match spec task IDs
    pointer_map_keys = set(pointer_map.keys())

    missing_in_map = task_ids_in_spec - pointer_map_keys
    extra_in_map = pointer_map_keys - task_ids_in_spec

    assert len(missing_in_map) == 0, f"Tasks in spec but not in pointer_map: {missing_in_map}"
    assert len(extra_in_map) == 0, f"Tasks in pointer_map but not in spec: {extra_in_map}"


def test_pointer_map_values_match_task_ptrs():
    """Test that pointer_map values match task ptr fields."""
    pointer_map_path = Path(__file__).parent.parent.parent / "spec/pointer_map.json"
    with open(pointer_map_path, encoding='utf-8') as f:
        pointer_map = json.load(f)

    spec_path = Path(__file__).parent.parent.parent / "spec/se_dsl_v1.spec.json"
    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)

    # Build task_id -> ptr mapping from spec
    spec_task_ptrs = {}
    for section in spec["sections"]:
        for task in section.get("tasks", []):
            spec_task_ptrs[task["id"]] = task["ptr"]

    # Compare with pointer_map
    mismatches = []
    for task_id, ptr in pointer_map.items():
        if task_id in spec_task_ptrs:
            if spec_task_ptrs[task_id] != ptr:
                mismatches.append(f"{task_id}: map={ptr}, spec={spec_task_ptrs[task_id]}")

    assert len(mismatches) == 0, f"Pointer mismatches: {mismatches}"
