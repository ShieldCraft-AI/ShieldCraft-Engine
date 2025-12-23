from shieldcraft.verification.test_coverage import check_checklist_test_coverage


def test_checklist_coverage_positive():
    items = [{"id": "a", "test_refs": ["t1"], "ptr": "/s/1"}]
    v = check_checklist_test_coverage(items)
    assert v == []


def test_checklist_coverage_negative():
    items = [{"id": "a", "test_refs": [], "ptr": "/s/1"}, {"id": "b", "ptr": "/s/2"}]
    v = check_checklist_test_coverage(items)
    assert len(v) == 2
    assert v[0]["reason"] == "missing_test_refs"
