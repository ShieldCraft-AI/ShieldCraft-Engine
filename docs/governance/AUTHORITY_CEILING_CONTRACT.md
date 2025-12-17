# AUTHORITY CEILING CONTRACT (AUTHORITATIVE)

This contract defines the authority ceilings for the compiler and enforces guard-only behavior: the compiler must never escalate authority beyond what the spec explicitly grants unless that escalation is exposed as a BLOCKER + DIAGNOSTIC and recorded in the run events.

Principles
- No new inference, synthesis, or heuristic behavior is permitted by this phase. Phase 12 is purely guard-and-enforcement.
- Tier A authority must not be silently resolved by the compiler. Any Tier A synthesis must be accompanied by an explicit BLOCKER event and a DIAGNOSTIC event for auditability.
- REFUSAL outcomes require explicit authority metadata (evidence.refusal.authority) and the compiler asserts its presence at finalization. REFUSAL must not be used to mask missing authority.

Enforcement
- Assertions are centralized in `finalize_checklist` to fail fast when authority ceilings are violated.
- Unit tests must verify that missing authority causes assertion failures rather than silent behavior.

Signed: Governance
Date: 2025-12-17
