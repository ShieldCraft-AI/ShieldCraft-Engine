# Persona Non-Authority Contract (AUTHORITATIVE)

Decision: AUTHORITATIVE — Persona Protocol Boundary Locked (Phase 15)

Summary
- Personas are scoped specialists that may provide annotations, diagnostics, or advisory constraints but MUST NOT act as implicit authorities that alter checklist semantics or outcomes.

Rules (authoritative)
- Personas may only emit audit events (annotations, persona events) and record vetoes for observability; vetoes MUST be treated as advisory (DIAGNOSTIC) and MUST NOT cause REFUSAL or BLOCKER behavior.
- Personas MUST NOT be permitted to directly mutate semantic fields that affect checklist primary outcome or refusal authority, including but not limited to: `id`, `ptr`, `generated`, `artifact`, `severity`, `refusal`, `outcome`.
- Persona constraints that attempt disallowed mutations MUST be recorded in `item.meta.persona_constraints_disallowed` and a `G15_PERSONA_CONSTRAINT_DISALLOWED` DIAGNOSTIC event MUST be emitted for visibility.
- Persona routing and evaluation order MUST be deterministic and recorded only as metadata or persona events; they MUST NOT influence primary checklist derivation.

Rationale
- Personas provide useful domain-specific advice and annotations but must not supplant governance or authority ceilings. Ensuring personas are advisory preserves auditability, reduces accidental refusal, and prevents stealth authority escalation.

Enforcement
- Implementation-level enforcement is via deterministic tests and lightweight runtime guards (recording disallowed attempts and converting previous persona veto raises into advisory DIAGNOSTIC events).
- Tests: `tests/persona/test_persona_protocol_boundary_routing_invariance.py`, `tests/persona/test_persona_decision_precedence.py`, `tests/persona/test_persona_non_interference_guards.py`, `tests/persona/test_persona_scale_order_invariance.py` verify contract requirements.

Cross-references
- AUTHORITY_CEILING_CONTRACT.md (persona outputs must respect authority ceilings)
- TEMPLATE_NON_AUTHORITY_CONTRACT.md (templates non-authoritative policy)

Status: AUTHORITATIVE (locked)
