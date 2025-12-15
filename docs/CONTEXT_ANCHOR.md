# ShieldCraft Engine — Context Anchor

## What This Project Is

- ShieldCraft Engine is a deterministic software manufacturing engine that validates canonical product specifications and produces auditable, reproducible build artifacts for review and CI.

## What Is Complete

- Canonical DSL and schema: `spec/se_dsl_v1.spec.json` and `spec/schemas/se_dsl_v1.schema.json`.
- Determinism tooling and checks: `scripts/canonical_full_run.py`, `scripts/canonicalize_spec.py`, and related tests (e.g., `tests/ci/test_canonical_full_run_regression.py`, `tests/spec/test_canonical_json.py`).
- Self-host dry-run and artifact emission tooling, including deterministic preview and manifest emission (see `src/shieldcraft/engine.py` and self-host scripts).
- Governance artifacts and audits: governance docs and audit script (`docs/governance/*`, `scripts/audit_docs.py`, `artifacts/governance/doc_classification_report.json`).
- Persona subsystem (opt-in) with non-interference rules and tests (`docs/persona/*`, persona code under `src/shieldcraft/persona`, and persona tests under `tests/persona/`).
- Test Attachment Contract (TAC) implemented as an opt-in enforcement (environment flag `SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT`) and related validators/tests present.
- Generated verification tests exist under `tests/generated/verification_spine/` and test-generation scripts under `scripts/`.

## What Is In Progress

- Phase 14 remediation: self-hosting validation failures are triaged and remediation work is started (`docs/governance/progress.md` shows `self-hosting-remediation: STARTED`).
- Consolidation of verification and governance documentation (e.g., `docs/governance/VERIFICATION_SPINE.md` added/expanded).
- Integrating determinism regression checks into CI (regression test added at `tests/ci/test_canonical_full_run_regression.py`).
- Implementation PRs for approved RFCs are being prepared (spec changes are approved; implementation work is tracked in `docs/governance/progress.md`).

## What Is Explicitly Not Done

- A formal progress/state file schema is not defined (`docs/governance/progress.md` lists this as an open gap).
- Remaining implementation of approved RFCs is pending review and PRs (the spec-level RFCs are approved; code/tests implementing them remain gated to PRs).
- Phase 14 self-hosting validation is not completed; failures remain and remediation is ongoing.

## Current Focus

- Current active phase: Verification / Testing Spine. This phase exists to ensure engine outputs meet structural, semantic, and determinism guarantees by running deterministic previews, emitting canonical digests, and producing audit-ready artifacts for CI and external validation (see `docs/governance/VERIFICATION_SPINE.md` and `docs/governance/progress.md`).

## How This File Is Used

- This file is an authoritative, short snapshot of repository state for use in conversation resets and onboarding. Update it only when factual repository state changes and record changes in `docs/governance/decision_log.md` and via `scripts/audit_docs.py`.
