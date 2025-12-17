from shieldcraft.engine import finalize_checklist


class DummyContext:
    def __init__(self):
        self._events = []

    def record_event(self, gate_id, phase, outcome, message=None, evidence=None):
        self._events.append({
            'gate_id': gate_id,
            'phase': phase,
            'outcome': outcome,
            'message': message,
            'evidence': evidence,
        })

    def get_events(self):
        return list(self._events)


class E:
    def __init__(self):
        self.checklist_context = DummyContext()


def test_primary_outcome_success_no_events():
    engine = E()
    res = finalize_checklist(engine)
    # No events and no items -> diagnostic by new contract
    assert res["primary_outcome"] == "DIAGNOSTIC"
    assert res["refusal"] is False


def test_primary_outcome_diagnostic_only():
    engine = E()
    engine.checklist_context.record_event("G6_VERIFICATION_SPINE_FAILURE", "preflight", "DIAGNOSTIC", message="d1")
    engine.checklist_context.record_event("G4_SCHEMA_VALIDATION", "preflight", "DIAGNOSTIC", message="d2")
    res = finalize_checklist(engine)
    assert res["primary_outcome"] == "DIAGNOSTIC"
    assert res["refusal"] is False


def test_primary_outcome_blocked():
    engine = E()
    engine.checklist_context.record_event("G9_GENERATOR_RUN_FUZZ_GATE", "generation", "BLOCKER", message="b1")
    res = finalize_checklist(engine)
    assert res["primary_outcome"] == "BLOCKED"
    assert res["refusal"] is False


def test_primary_outcome_refusal_takes_precedence():
    engine = E()
    engine.checklist_context.record_event("G14_SELFHOST_INPUT_SANDBOX", "post_generation", "REFUSAL", message="r1")
    engine.checklist_context.record_event("G9_GENERATOR_RUN_FUZZ_GATE", "generation", "BLOCKER", message="b1")
    res = finalize_checklist(engine)
    assert res["primary_outcome"] == "REFUSAL"
    assert res["refusal"] is True


def test_mixed_non_diagnostic_treated_as_success():
    engine = E()
    # event with unknown/other outcome considered informational -> diagnostic under new contract
    engine.checklist_context.record_event("G_X_INFO", "post", "INFO", message="i1")
    res = finalize_checklist(engine)
    assert res["primary_outcome"] == "DIAGNOSTIC"
    assert res["refusal"] is False
