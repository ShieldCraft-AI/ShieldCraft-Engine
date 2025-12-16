Decision Log

This file records major governance decisions and rationale for the ShieldCraft
project. It exists to satisfy governance artifact checks used by the engine's
test suite and CI. No production semantics are contained here; it is intentionally
minimal for CI verification.
# RFC Decision Log

Authoritative decisions made on 2025-12-13 (Phase 13 kickoff). All decisions recorded are spec-only; implementation requires separate PRs referencing RFC approvals.

## rfc-generator-version-contract.md
- Decision: APPROVE
- Rationale: A strict generator lockfile and `metadata.generator_version` requirement enforce reproducibility and CI safety. Explicit `generator_version` reduces surprises in preflight and ensures traceability.
- Effective scope: Spec-only; requires linter/migration guidance and CLI flags for a migration window.
- Blocking dependencies: `generators/lockfile.json` management and CI upgrade; adoption plan must include a migration tool.

## rfc-allowed-checklist-types.md
- Decision: APPROVE (with migration guard)
- Rationale: A canonical `type` enum prevents ad-hoc types and supports deterministic codegen and classification.
- Effective scope: Spec-only (schema change); migration scripts and `--lenient-types` flag should be implemented in a follow-up PR.
- Blocking dependencies: Adoption plan for migration, PRs to update schema and linter rules.

## rfc-pointer-map-semantics.md
- Decision: APPROVE
- Rationale: Canonical id-based pointers for arrays improve readability and determinism; providing `raw_ptr` ensures backward compatibility for consumers of numeric indices.
- Effective scope: Spec-only; requires pointer_map migration and test fixture updates.
- Blocking dependencies: Migration scripts to map numeric pointers to canonical pointers, and update pointer_map consumers.

## rfc-checklist-pointer-normalization.md
- Decision: APPROVE
- Rationale: Checklist extraction should include scalar leaf nodes and `requires_code` to enable correct codegen routing and ensure no items are inadvertently omitted.
- Effective scope: Spec-only; affects checklist schema and generator preflight validation.
- Blocking dependencies: Pointer map semantics RFC and allowed types RFC (to determine classification rules).

## rfc-bootstrap-artifacts.md
- Decision: APPROVE
- Rationale: Clear bootstrap artifact emission semantics reduce ambiguity and ensure self-host runs produce predictable bootstrap outputs and `summary.json` for CI/instrumentation.
- Effective scope: Spec-only; impacts self-host run contract and generator preflight.
- Blocking dependencies: Allowed checklist types RFC (defines bootstrap types), pointer normalization RFC (ensures pointer mapping for bootstrap tasks).

## Audit: Check for unambiguous decision status
- All RFCs above are provided with explicit decisions and rationale. There are no implicit approvals.
- Deferred RFCs: None.