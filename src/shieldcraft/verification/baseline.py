from .properties import VerificationProperty
from .registry import global_registry
from .scopes import VerificationScope


BASELINE_PROPERTIES = [
    VerificationProperty(
        id="VP-01-SPEC-TRACEABLE",
        description="Spec artifacts are traceable and fingerprinted.",
        scope=VerificationScope.SPEC.value,
        severity="high",
        deterministic=True,
    ),
    VerificationProperty(
        id="VP-02-CHECKLIST-COMPLETE",
        description="Checklist preflight includes required validation artifacts and passes.",
        scope=VerificationScope.CHECKLIST.value,
        severity="medium",
        deterministic=True,
    ),
    VerificationProperty(
        id="VP-03-NO-UNKNOWN-OUTPUTS",
        description="Outputs contain only known fields and types per manifest schema.",
        scope=VerificationScope.OUTPUT.value,
        severity="high",
        deterministic=True,
    ),
    VerificationProperty(
        id="VP-04-PERSONA-NON-AUTHORITY",
        description="Persona outputs are advisory and not authoritative; they do not confer approvals.",
        scope=VerificationScope.PERSONA.value,
        severity="medium",
        deterministic=True,
    ),
    VerificationProperty(
        id="VP-05-SPEC-CHECKLIST-TRACE_COMPLETE",
        description="All checklist items must have explicit, valid spec pointers (spec_pointer).",
        scope=VerificationScope.CHECKLIST.value,
        severity="error",
        deterministic=True,
    ),
]


def _register_baseline():
    reg = global_registry()
    for p in BASELINE_PROPERTIES:
        try:
            reg.register(p)
        except ValueError:
            # Already registered — idempotent
            pass


_register_baseline()
