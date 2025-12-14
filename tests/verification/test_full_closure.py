from shieldcraft.services.ast.builder import ASTBuilder
from shieldcraft.verification.spec_to_checklist import check_spec_to_checklist
from shieldcraft.verification.checklist_to_test import check_checklist_to_test
from shieldcraft.verification.test_to_artifact import check_test_to_artifact, check_orphan_artifacts


def test_full_closure_positive():
    # Build minimal spec with one section
    spec = {"sections": {"1": {"id": "s1", "description": "sec"}}}
    ast = ASTBuilder().build(spec)

    # Checklist item referencing the section
    checklist = [{"id": "c1", "ptr": "/sections/1", "test_refs": ["test::t1"]}]

    # Test registry and artifact mapping
    tests = {"test::t1": "tests/test_sample.py::test_example"}
    test_artifact_map = {"test::t1": ["artifacts/manifest.json"]}
    artifacts = ["artifacts/manifest.json"]

    # Run verifiers
    spec_v = check_spec_to_checklist(ast, checklist)
    chk_v = check_checklist_to_test(checklist)
    t_v = check_test_to_artifact(tests, test_artifact_map)
    a_v = check_orphan_artifacts(artifacts, test_artifact_map)

    assert spec_v == []
    assert chk_v == []
    assert t_v == []
    assert a_v == []


def test_full_closure_negative():
    spec = {"sections": {"1": {"id": "s1", "description": "sec"}, "2": {"id": "s2"}}}
    ast = ASTBuilder().build(spec)

    # Checklist only covers section 1, missing section 2
    checklist = [{"id": "c1", "ptr": "/sections/1", "test_refs": []}]

    tests = {"test::t1": "tests/test_sample.py::test_example"}
    test_artifact_map = {}  # no artifacts referenced
    artifacts = ["artifacts/unused.json"]

    spec_v = check_spec_to_checklist(ast, checklist)
    chk_v = check_checklist_to_test(checklist)
    t_v = check_test_to_artifact(tests, test_artifact_map)
    a_v = check_orphan_artifacts(artifacts, test_artifact_map)

    assert len(spec_v) == 1
    assert spec_v[0]["reason"] == "orphan_spec_clause"

    # checklist should report missing test refs
    assert len(chk_v) == 1
    assert chk_v[0]["reason"] == "missing_test_refs"

    # tests without artifacts -> violation
    assert len(t_v) == 1
    assert t_v[0]["reason"] == "missing_artifact_refs"

    # artifact is orphan
    assert len(a_v) == 1
    assert a_v[0]["reason"] == "orphan_artifact"
