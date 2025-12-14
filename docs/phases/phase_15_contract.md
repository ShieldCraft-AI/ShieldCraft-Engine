# Phase 15 — Self-Hosting Remediation Contract

Phase name: self-hosting-remediation (Phase 15)

## Objective
- Remediate the blocking defects discovered during Phase 14 self-hosting validation so the self-host pipeline deterministically passes the full test suite and artifact validation.

## Scope and Allowed Actions
- Allowed actions:
  - Targeted code fixes mapped to triaged failure categories in `docs/self_hosting_failure_triage.md`.
  - Spec/schema changes where explicitly required to resolve contract mismatches; spec changes must follow the spec-first rule and correspond to an RFC or a patch entry created by the product team.
  - Test updates or additions that validate the intended authoritative behavior.
  - Backwards-compatibility guards (e.g., feature flags, migration environment variables) where the fix would otherwise break legacy behavior.
- Forbidden actions:
  - No new features, DSL extensions, or broad refactors unrelated to the triaged categories.
  - No cross-RFC work; a PR must implement a single triaged failure category or a single RFC.

## Process Rules
- One triaged failure category per PR. A PR can include multiple tests and small refactors that directly support that single category, but not multi-category changes.
- Spec-first rule: If a change requires a spec update, the first commit in the PR must be the spec/schema change, followed by code and test changes implementing it.
- PRs must include a deterministic test harness showing deterministic outputs remain stable (self-host manifest/hash comparison) and a CI run with pytest -q passing for modified areas.
- Migration guards: If a fix alters default behavior for older specs, include a guard (environment variable or `feature_gate` in metadata) and tests that show both migration and canonical behavior.
- Backwards-compatibility: Ensure code remains compatible with canonical DSL; test both canonical and sample legacy specs preserved by migration guard.

## Determinism and Compatibility Requirements
- Determinism: The self-host run must produce byte-for-byte identical `manifest.json` and `summary.json` hashes across repeated runs on the same environment and spec.
- No randomization: No runtime timestamps or environment-based paths should pollute deterministic artifacts.
- Compatibility: When changes break legacy flows, a migration guard must be provided and the documentation updated.

## Entry Conditions
- `docs/self_hosting_failure_triage.md` and `docs/phase_14_closure.md` exist and are authoritative snapshots of the triage and closure.
- PRs must be scoped to a single triaged failure category and include the spec-first commit when required.
- No new RFCs outside the triage scope should be introduced in Phase 15.

## Exit Criteria
- All triaged failure categories marked as remediated with passing PRs.
- Full test suite (`pytest -q`) passes locally and in CI, including the deterministic self-host run run twice with identical artifacts.
- Updated migration guidance and docs where backward compatibility guards are provided.
- All changes merged into a Phase 15 `remediation` branch and tested in the CI pipeline before re-attempting Phase 14 validation.

## Governance
- Approvals required: Code changes must pass a code review by the engineering lead and a spec validation review if spec changes are included.
- All PRs must include tests that reproduce the original failure and validate the remediation.

## Priorities
- Fixes are prioritized in the following order:
  1. Generator lockfile / preflight contract behavior
  2. Engine/DSL mapping (`spec_format` => `dsl_version` mapping)
  3. Evidence bundle compatibility
  4. Codegen output shape standardization
  5. Pointer map canonicalization
  6. Pointer coverage shape
  7. Checklist ID canonicalization
  8. JSON canonical formatting
  9. Cross-section types enforcement
  10. Self-host summary completeness

