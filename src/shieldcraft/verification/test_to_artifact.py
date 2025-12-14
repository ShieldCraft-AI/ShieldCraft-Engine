from typing import List, Dict


def check_test_to_artifact(tests: Dict[str, str], test_artifact_map: Dict[str, List[str]]) -> List[Dict]:
    """Verify each test references >=1 artifact path or manifest entry.

    `tests` is mapping test_id -> test_ref
    `test_artifact_map` is mapping test_id -> list of artifact paths
    """
    violations = []
    for tid in sorted(tests.keys()):
        artifacts = test_artifact_map.get(tid, [])
        if not artifacts:
            violations.append({"test_id": tid, "reason": "missing_artifact_refs"})
    return violations


def check_orphan_artifacts(all_artifacts: List[str], test_artifact_map: Dict[str, List[str]]) -> List[Dict]:
    """Detect artifacts not referenced by any test."""
    referenced = set()
    for arts in test_artifact_map.values():
        for a in arts:
            referenced.add(a)

    violations = []
    for a in sorted(all_artifacts):
        if a not in referenced:
            violations.append({"artifact": a, "reason": "orphan_artifact"})

    return violations
