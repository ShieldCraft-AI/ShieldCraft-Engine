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
