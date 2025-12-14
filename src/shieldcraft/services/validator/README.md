# Instruction Validator

This module provides deterministic validation for instruction blocks in product specs.

Purpose:
- Validate that a spec's `invariants` and `instructions` conform to the minimal runtime contract.
- Provide a single, non-bypassable entrypoint for the engine to enforce instruction-level invariants.

Contract:
- Use `validate_instruction_block(spec)` as the canonical, public entrypoint.
- Validation is deterministic and raises `ValidationError` on violations.
- Validation error objects carry `code`, `message`, and `location` and are stable across runs.

Non-bypassable semantics:
- The `Engine` calls the validator early in its pipeline (preflight) and records a deterministic
  fingerprint of validated specs. Execution paths assert that validation occurred for the
  spec being processed.

Error codes:
- See `VALIDATION_ERROR_CODES` in the module for the frozen set of allowed error codes.
