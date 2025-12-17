# Refusal Authority Contract (AUTHORITATIVE)

Decision date: 2025-12-17

Summary
- This contract establishes an authoritative mapping from REFUSAL gate identifiers
  (e.g., `G2_GOVERNANCE_PRESENCE_CHECK`) to named refusal authorities
  (e.g., `governance`, `persona`, `infrastructure`).
- Every REFUSAL event emitted by the engine MUST include structured refusal
  metadata in its `evidence.refusal` object with keys: `authority`, `trigger`,
  `scope`, and `justification`.

Requirements
- The codebase provides a deterministic map in `src/shieldcraft/services/governance/refusal_authority.py`.
- The helper `record_refusal_event(context, gate_id, phase, ...)` must be used
  to record REFUSALs at known gates and attaches the required `refusal` metadata.
- The finalization boundary (`finalize_checklist`) asserts that any REFUSAL in the
  finalized events includes a valid, non-empty `authority` string and surfaces
  the authority as `checklist.refusal_authority`.

Rationale
- Explicit authority attribution enables auditability, makes REFUSALs
  inspectable by automated tools, and reduces ambiguity in governance decisions.
- Structured refusal metadata enables paired diagnostics for missing authority
  cases and deterministic diagnostics masking.

Enforcement
- Code-level assertions validate presence and type of `authority` during
  checklist finalization.
- Unit tests (`tests/test_refusal_authority.py`) cover normal and failure modes.
- CI guards must include `tests/ci/test_refusal_authority_persistence.py` to ensure
  the authoritative map covers known REFUSAL gates used by the engine.

Scope
- This contract is AUTHORITATIVE for REFUSAL metadata assignment. Any future
  edits to gate→authority mappings require an explicit decision recorded in
  `docs/governance/decision_log.md`.

Owners
- Governance (docs/governance)
