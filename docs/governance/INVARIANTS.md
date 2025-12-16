# Invariants (ShieldCraft Engine v1)

This file defines non-negotiable invariants of the ShieldCraft Engine (SE).
An invariant expresses a condition that must always hold, how violations are classified,
and what actions are permitted or forbidden in response.

Each invariant is enforced in exactly one authoritative location.
No invariant may be enforced implicitly or redundantly.

---

## Invariant Enforcement Map

- Instruction invariants  
  Enforced in: `shieldcraft.services.validator.validate_spec_instructions`

- Repository sync invariants  
  Enforced in: `shieldcraft.services.sync.verify_repo_sync`  
  Violation surfaced as: `SyncError`

- Pointer coverage invariants  
  Enforced in: `shieldcraft.services.spec.pointer_auditor.ensure_full_pointer_coverage`  
  Used during: preflight

- Checklist must/forbid invariants  
  Evaluated in: `ChecklistGenerator.build` via `invariants.evaluate_invariant`  
  Enforcement resides in: checklist generation and derived resolution

- Test Attachment Contract (TAC v1)  
  Authoritative doc: `docs/governance/TEST_ATTACHMENT_CONTRACT.md`  
  Enforcement point: `shieldcraft.services.validator.tests_attached_validator.verify_tests_attached` (preflight gate)

- tests_attached_opt_in
  - Enforced when:
    - `env:SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT`
    - `spec.metadata.enforce_tests_attached`
  - Failure class: `PRODUCT_INVARIANT_FAILURE`
  - Default behavior: non-blocking (opt-in)

- Self-host artifact emission invariants  
  Enforced in: `Engine.run_self_host` using `is_allowed_selfhost_path()`

---

## Failure Classification Invariants

### Failure Classes (Exhaustive)

All failures in SE **must** be classified as exactly one of the following:

- `PRODUCT_INVARIANT_FAILURE`
- `SPEC_CONTRACT_FAILURE`
- `SYNC_DRIFT_FAILURE`
- `ORCHESTRATION_FAILURE`
- `UNKNOWN_FAILURE`

No other failure classes are permitted.

Failure classification is mandatory before any corrective action.

---

### ORCHESTRATION_FAILURE

An `ORCHESTRATION_FAILURE` applies when **all** of the following are true:

- The failure occurs before SE product logic executes.
- The failure originates from the orchestration or execution environment.
- No product artifact hash, spec, checklist, or invariant is violated.

Examples (non-exhaustive):
- Missing tooling (e.g. pytest not installed)
- Missing or incorrect environment setup
- Invalid CI workflow configuration
- Runner, permission, or infrastructure misconfiguration

---

## Enforcement Rules

- Product code **must not** be modified in response to an `ORCHESTRATION_FAILURE`.
- Only orchestration-layer artifacts (e.g. CI workflows, runners, environment setup)
  may be changed.
- Resolution of an `ORCHESTRATION_FAILURE` is required before any product-level
  work may proceed.

---

## Persona Constraints

- Personas **must** classify the failure before emitting guidance.
- Personas **must not** recommend product-level changes until failure class
  is determined.
- If the failure class is `ORCHESTRATION_FAILURE`:
  - Personas **must refuse** product-level recommendations.
  - Persona output is restricted to orchestration-layer observations or vetoes.

Persona output is data, not inference.

---

## Persona Governance Invariants

- **ExecutionMode locking requirement**: Persona activation and operation are permitted only when the runtime `ExecutionMode` explicitly allows persona activity; persona behavior must never rely on ambient or implicit execution mode settings.
- **Mandatory Failure Classification Gate**: Personas must not emit recommendations or approvals until a failure has been classified per the Failure Classification Gate.
- **Persona Decision Record (PDR) requirement**: All persona decisions (annotations, vetoes, recommendations) that affect operational choices MUST be recorded as a Persona Decision Record (PDR) and linked to the corresponding persona event in `artifacts/persona_events_v1.json`.
- **Prohibition of runtime flags encoding process state**: Runtime flags and ad-hoc environment variables MUST NOT be used to encode or convey protocol or process state; protocol state belongs in explicit, auditable records (e.g., PDRs and persona events).
- **Mandatory refusal and pushback behavior**: When a request violates an invariant, Failure Classification Gate, or ExecutionMode rules, personas MUST refuse and provide structured pushback according to `PERSONA_PROTOCOL.md`.

Reference: PERSONA_PROTOCOL.md is the single source of truth for persona governance and binding protocol rules.

## Failure Classification Gate

After any CI or execution failure:

- Evidence **must** be collected.
- Failure **must** be classified into exactly one failure class.
- No instruction block may be issued before classification is recorded.

---

## CI Assumption Invariant

CI workflows **must not** assume project structure or implicit tooling.

Forbidden assumptions include:
- Presence of `requirements.txt`
- Implicit availability of pytest or global tools

All CI setup **must** derive from:
- `pyproject.toml`
- Explicit, versioned installation steps

Violation of this invariant is classified as `ORCHESTRATION_FAILURE`.

---

## Unknown Failures

Any failure that cannot be deterministically classified **must** be classified as
`UNKNOWN_FAILURE`.

On `UNKNOWN_FAILURE`:
- All progress halts.
- Escalation is mandatory.
- No speculative fixes are permitted.

---

## Verification Spine

Verification-related invariants and properties are to be enforced by the Verification Spine (see `docs/governance/VERIFICATION_SPINE.md` and `src/shieldcraft/verification`).

This file declares the governance anchor; enforcement logic will be implemented in the Verification Spine and versioned via its governance document.

---

## Checklist Emission Invariant

- All engine execution paths MUST result in a finalized checklist artifact (final checklist or explicit refusal) that records the observed gate events. The canonical emission boundary is the centralized function `finalize_checklist(...)` in `src/shieldcraft/engine.py`.
- Exceptions may occur only after recording a gate event to the `ChecklistContext`.
- `finalize_checklist(...)` is the sole emission boundary.
- This invariant is enforced by code-level assertions and tests.

## Semantic Outcome Invariants (Phase 5)

- Statement: Every emitted checklist MUST contain a single canonical `primary_outcome` with value one of: `SUCCESS`, `REFUSAL`, `BLOCKED`, `DIAGNOSTIC_ONLY`.
- Role assignment: Each checklist item MUST be assigned exactly one `role` drawn from: `PRIMARY_CAUSE`, `CONTRIBUTING_BLOCKER`, `SECONDARY_DIAGNOSTIC`, `INFORMATIONAL`.
- Mapping rules:
  - `REFUSAL` if any recorded event has outcome `REFUSAL`.
  - `BLOCKED` if no `REFUSAL` and any recorded event has outcome `BLOCKER`.
  - `DIAGNOSTIC_ONLY` if all recorded events are `DIAGNOSTIC`.
  - `SUCCESS` if there are no events or only informational/non-diagnostic events.
- Semantic invariants (enforced in `finalize_checklist`):
  - Exactly one `PRIMARY_CAUSE` item MUST exist unless `primary_outcome == SUCCESS`.
  - `REFUSAL` outcome MUST include `refusal_reason` and top-level `refusal == true`.
  - `BLOCKED` outcome MUST NOT set `refusal == true`.
  - `DIAGNOSTIC_ONLY` outcome MUST NOT contain `BLOCKER` or `REFUSAL` items.
- Enforcement: These invariants are enforced by code-level assertions inside `finalize_checklist` and protected by deterministic, unit-tested behavior.

- Semantic Outcome Lock: The canonical semantics (primary outcome derivation, item roles, and invariants) are locked under Phase 5 and may not be altered except via an explicit governance phase update. Changes to semantic meaning require a recorded governance decision and a corresponding implementation phase.

