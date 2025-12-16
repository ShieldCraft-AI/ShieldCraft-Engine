# Spec → Checklist Compiler (AUTHORITATIVE)

This document defines the authoritative boundary, responsibilities, and contract for the Spec → Checklist compiler subsystem implemented by `ChecklistGenerator.build` in `src/shieldcraft/services/checklist/generator.py`.

Purpose
- The compiler deterministically synthesizes a finalized checklist artifact (the *checklist result object*) from a canonical spec input. It is NOT an executor: it must not perform build, test, nor deployment actions.

Inputs (canonical)
- A canonical spec (loaded by `shieldcraft.dsl.loader.load_spec`) represented as a dict.
- Optional: an AST produced by `shieldcraft.services.ast.builder.ASTBuilder` to avoid re-parsing.
- Optional: configuration flags (e.g., `dry_run`, `run_test_gate`, `run_fuzz`) that influence internal validation, but do not change the compilation contract.

Guaranteed Outputs
- The compiler always returns a serializable result dict. In normal operation this object contains at minimum:
  - `items`: list of synthesized checklist items (possibly empty)
  - `valid`: boolean indicating contract success (True/False)
  - `preflight`: preflight summary
  - `invariant_violations` / `invariants_ok` when applicable
  - Persisted artifacts such as manifest/lineage when `dry_run=False`

- The compiler never silently suppresses emission: a caller may obtain a partial or invalid result (`valid == False`) but will always receive an emitted result object describing the compiler outcome.

Explicit Non-Responsibilities
- The compiler MUST NOT: execute tests, produce build artifacts, or mutate external state beyond deterministic, auditable artifact writing (manifests, canonical JSON) and warnings. Active execution responsibilities belong to the execution subsystem.

Auditing and Determinism
- All compiler-internal events that represent gating decisions (e.g., preflight failures, contract violations) must be recorded through the provided `ChecklistContext` (if present) so callers may derive a canonical run artifact via `finalize_checklist(...)`.
- The compiler must avoid non-deterministic side effects (randomness without seeded determinism, reliance on external time or ephemeral state) in its canonical output.

Scope
- This document formalizes the contract only. Behavioral changes, schema evolution, or persona changes require an explicit governance phase and are out of scope for Phase 8.
