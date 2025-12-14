**Engine Contract (v1)**

Summary:

- The Engine guarantees: validation against the canonical DSL, deterministic generation (when configured), and auditable artifact emission for self-host runs.

Responsibilities:

- Validate input specs against `spec/schemas/se_dsl_v1.schema.json` before building ASTs.
- Emit deterministic artifacts (manifest.json, summary.json, canonical_preview.json) when `determinism` is required by spec metadata.
- Respect opt-in enforcement flags (e.g., TAC via `SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT`).

Failure semantics:

- Determinism violations are considered CI-blocking unless explicitly allowlisted in governance contracts.
- Validation failures should surface as `schema_error` with a clear error payload.

Observability & audit:

- The engine writes determinism snapshots and emits readiness state for external monitoring. Forensic bundles are produced for self-build mismatches.
