from shieldcraft.verification.spec_trace import check_spec_checklist_trace


def test_spec_trace_positive():
    items = [
        {"id": "a", "spec_pointer": "/sections/1", "ptr": "/sections/1"},
        {"id": "b", "spec_pointer": "/sections/2", "ptr": "/sections/2"},
    ]
    violations = check_spec_checklist_trace(items)
    assert violations == []


def test_spec_trace_negative():
    items = [
        {"id": "a", "ptr": "/sections/1"},  # missing spec_pointer
        {"id": "b", "spec_pointer": "not/a/pointer", "ptr": "/sections/2"},
    ]
    violations = check_spec_checklist_trace(items)
    assert len(violations) == 2
    assert violations[0]["reason"] == "invalid_or_missing_spec_pointer"
