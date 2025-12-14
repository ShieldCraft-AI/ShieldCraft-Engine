# ShieldCraft Instruction Invariants v1

This document defines the core invariants to follow when writing or executing construction instructions (checklist/build steps) in the ShieldCraft ecosystem. These invariants are required to ensure deterministic, auditable, and canonical behavior of the engine, checklist generation, and code output.

## Invariant preamble (required for all construction paths)

- No ambient state: Instructions must not depend on or embed spin-up time, current timestamps, environment-specific values, or uncontrolled randomness. All time-dependent or random behavior must be injected explicitly as parameters or normalized during canonicalization.

- Stable ordering: All collection ordering in outputs must be deterministic and sorted. When iterating or serializing dictionaries or lists that are used as canonical artifacts, keys and elements must be sorted or otherwise stable and reproducible across runs.

- Deterministic serialization: All produced artifacts (manifests, code bundles, checklists, and fingerprints) must be produced using deterministic serialization routines (canonical JSON, fixed float precision, and canonical hashing functions). No platform-dependent ordering or serialization formatting may be used.

- Single canonical DSL: The canonical DSL for production work is `spec/schemas/se_dsl_v1.schema.json`. All production specs must declare `dsl_version` set to the canonical version and conform to the canonical schema; no fallback to legacy, ambiguous, or multiple DSL flavors is permitted for new specs.

- No implicit defaults: Construction steps must not rely on implicit defaults baked in code or environment if those defaults can vary. Defaults are allowed, but they must be explicit in the spec or canonicalized prior to use.

## Implementation guidance

- Always use `extract_json_pointers()` and canonical pointer mapping when referencing spec locations.
- When serializing for the manifest or artifacts, use `write_canonical_json()` or equivalent to ensure deterministic formatting.
- Any tests or harnesses that verify determinism should intentionally fix seeds, float precision, or timestamps (or use canonicalization) to ensure reproducible run artifacts.

## Verification Requirements

- Determinism tests should assert equality of digest/fingerprint outputs across multiple runs.
- Lineage tests should assert that every AST node that has a `ptr` has a stable `lineage_id` and that lineage IDs are propagated to derived tasks and codegen artifacts.
- Pointer audits should validate that pointer formats follow the canonical pointer mapping (including id-based array pointer behavior for lists of objects with `id`).

## Non-conformance

If a preflight, determinism or pointer audit fails, stop generation and report: what field caused it, the pointer, and the canonical assertion that failed. Non-conforming specs are rejected until they are canonicalized.

---

This file encodes the project-level instruction invariants (v1). When the team evolves this contract, bump the `v1` tag and define a migration plan in docs/se_instruction_invariants_v2.md.