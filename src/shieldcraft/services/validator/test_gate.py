from typing import List
from shieldcraft.verification.test_registry import discover_tests
from shieldcraft.verification.checklist_test_contract import validate_test_contract


def enforce_tests_attached(items: List[dict]) -> None:
    """Ensure every checklist item has attached test_refs and those refs exist in test registry.

    Raises RuntimeError with list of missing item ids.
    """
    # Validate contract first
    violations = validate_test_contract(items)
    if violations:
        missing_ids = [v.get("id") for v in violations]
        raise RuntimeError(f"missing_test_refs:{missing_ids}")

    # Discover tests and validate refs
    test_map = discover_tests()
    missing_refs = []
    for it in items:
        for ref in it.get("test_refs", []):
            if ref not in test_map:
                missing_refs.append({"item_id": it.get("id"), "missing_ref": ref})

    if missing_refs:
        raise RuntimeError(f"invalid_test_refs:{missing_refs}")
