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


def test_schema_validation_emits_checklist():
    engine = E()
    # Simulate schema diagnostic event (G4)
    engine.checklist_context.record_event("G4_SCHEMA_VALIDATION", "preflight", "DIAGNOSTIC", message="schema failure")

    result = finalize_checklist(engine, partial_result={"type": "schema_error", "details": ["err"]})

    assert result["emitted"] is True
    assert "checklist" in result
    assert result["checklist"]["items"] or result["checklist"].get("refusal") is not None


def test_generator_blocker_emits_checklist():
    engine = E()
    # Simulate generator blocker gate (G9)
    engine.checklist_context.record_event("G9_GENERATOR_RUN_FUZZ_GATE", "generation", "BLOCKER", message="fuzz failed")

    partial = {"valid": False, "reason": "spec_fuzz_stability_failed", "items": [], "preflight": {}}
    result = finalize_checklist(engine, partial_result=partial)

    assert result["emitted"] is True
    assert "checklist" in result
    # Ensure that either checklist items recorded or a refusal flag exists
    assert result["checklist"]["items"] or result["checklist"].get("refusal") is not None


def test_selfhost_refusal_emits_checklist():
    engine = E()
    # Simulate a self-host refusal (G14)
    engine.checklist_context.record_event(
        "G14_SELFHOST_INPUT_SANDBOX",
        "post_generation",
        "REFUSAL",
        message="disallowed self-host input")

    result = finalize_checklist(engine)

    assert result["emitted"] is True
    assert "checklist" in result
    assert result["checklist"].get("refusal") is True
    assert result["checklist"].get("refusal_reason") is not None


def test_internal_exception_emits_checklist():
    engine = E()

    exc = RuntimeError("boom")
    result = finalize_checklist(engine, partial_result=None, exception=exc)

    assert result["emitted"] is True
    assert "checklist" in result
    # internal_exception should be represented in checklist items
    items = result["checklist"].get("items", [])
    assert any((it.get("text", "").startswith("internal_exception")) for it in items)
    assert result.get("error") is not None
