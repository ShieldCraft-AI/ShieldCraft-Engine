# Verification Spine (v1)

The Verification Spine is a first-class governance subsystem of ShieldCraft Engine.

Purpose:

- **Goal:** Ensure outputs from the ShieldCraft pipeline meet structural, semantic, and determinism guarantees required for decision-grade artifacts.
- **Scope:** Specification validation, checklist verification, determinism snapshots, readiness evaluation, and artifact-level parity checks.

Responsibilities:

- **Define** blocking and advisory verification gates.
- **Emit** deterministic snapshots and canonical digests for regression tests.
- **Provide** audit-friendly artifacts for external validation (summary.json, manifest.json, canonical_preview.json).

Artifacts:

- `summary.json`: run-level metrics and determinism flag.
- `canonical_preview.json`: canonicalized preview payload used for byte-level determinism checks.
- `generated_checklist.json`: checklist items used for verification and test generation.
- `persona_events_v1.json`: persona event traces when persona is enabled.

Decision points and owners:

- **Verification Owner:** `verification@shieldcraft` (team-level owner responsible for policy and CI gating).
- **Determinism Policy:** Engine and spec maintainers. Determinism violations are treated as CI-blocking regressions unless an allowlist is in place.

Enforcement:

- Verification is applied at preflight and self-host stages. Blocking invariants are enforced only when configured via TAC or authoritative spec flags.

See also: `docs/governance/CONTRACTS.md`, `docs/persona/PERSONA_PROTOCOL.md`, and `spec/se_dsl_v1.spec.json` for concrete contracts.
