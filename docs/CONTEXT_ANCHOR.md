# ShieldCraft Engine — Context Anchor

## Domain Map

- **Engine Core**
	- Authoritative: `src/shieldcraft/engine.py`, `src/shieldcraft/main.py`
	- Supporting: `src/shieldcraft/services/*`, `src/shieldcraft/dsl/*`
- **DSL / Spec**
	- Authoritative: `spec/se_dsl_v1.spec.json`, `spec/schemas/se_dsl_v1.schema.json`, `spec/se_dsl_v1.template.json`
	- Supporting: `spec/README.md`, `spec/pointer_map.json`
- **Checklist**
	- Authoritative: `src/shieldcraft/services/checklist/generator.py`, `src/shieldcraft/services/checklist/*`
	- Tests: `tests/checklist/*`
- **Verification**
	- Authoritative: `src/shieldcraft/verification/*`, `docs/governance/VERIFICATION_SPINE.md`
	- Tools: `scripts/canonical_full_run.py`, `scripts/canonicalize_spec.py`
- **Persona**
	- Authoritative: `src/shieldcraft/persona/__init__.py`, `src/shieldcraft/persona/persona_evaluator.py`, `docs/persona/PERSONA_PROTOCOL.md`
	- Tests: `tests/persona/*`
- **Governance**
	- Authoritative: `docs/governance/decision_log.md`, `docs/governance/INVARIANTS.md`, `docs/governance/OPERATIONAL_READINESS.md`, `docs/governance/CONTRACTS.md`, `docs/governance/progress.md`
	- Audit tooling: `scripts/audit_docs.py`, `artifacts/governance/doc_classification_report.json`

## Execution Flow (fact-backed)

- **Spec ingestion** — `load_spec()` used in `engine.execute()`; canonical loader in `src/shieldcraft/dsl/canonical_loader.py` (tests: `tests/spec/test_canonical_loader_roundtrip.py`).
- **Validation** — `validate_spec_against_schema(spec, schema_path)` in `engine.execute()` (schema: `spec/schemas/se_dsl_v1.schema.json`); instruction validation via `_validate_spec(spec)` in `engine.run_self_host()` and `engine.execute()`.
- **Checklist synthesis** — `self.checklist_gen.build(spec, ast=ast, engine=self)` (implementation: `src/shieldcraft/services/checklist/generator.py`).
- **Verification gates** — determinism snapshots via `src/shieldcraft/verification/seed_manager.py` (engine attaches `_determinism`); readiness via `src/shieldcraft/verification/readiness_evaluator.py` and `readiness_report.py`.
- **Self-host preview** — `engine.run_self_host(spec, dry_run=True, emit_preview=...)` returns `preview`; validated by `src/shieldcraft/services/selfhost/preview_validator.py`.
- **Artifact emission** — on non-dry-run: builds `.selfhost_outputs/{fingerprint}`, writes `bootstrap_manifest.json` and `repo_snapshot.json` (see `engine.run_self_host()`).
- **Determinism comparison** — `scripts/canonical_full_run.py` canonicalizes previews and compares `canonical_preview.json`; regression test: `tests/ci/test_canonical_full_run_regression.py`.

## Persona Protocol (implementation facts)

- **Activation** — opt-in via `SHIELDCRAFT_PERSONA_ENABLED` (`src/shieldcraft/persona/__init__.py`).
- **Loading** — engine calls `find_persona_files` / `resolve_persona_files` and may set `self.persona` to a `PersonaContext` in `engine.run_self_host()` when enabled.
- **Non-interference** — persona evaluator is non-mutating (`src/shieldcraft/persona/persona_evaluator.py`); persona events are data-only (`docs/persona/legacy/PERSONA_EVENTS.md`); tests enforce behavior (`tests/persona/*`).
- **Veto/Refusal** — persona veto exists as a terminal refusal path (docs and tests: `PERSONA_EVENTS.md`, `tests/persona/test_persona_veto.py`).

## Verification Spine (invariants, enforcement, tests)

- **Determinism**
	- Defined: `spec/schemas/se_dsl_v1.schema.json` (determinism section); `spec/se_dsl_v1.spec.json` includes determinism tasks.
	- Enforcement: `src/shieldcraft/verification/determinism_contract.py`, `seed_manager.py`, and `engine.run_self_host()` canonicalization/header injection.
	- Tests: `tests/ci/test_canonical_full_run_regression.py`, `tests/spec/test_canonical_json.py`, `tests/verification/test_seed_stability.py`.
- **Test Attachment Contract (TAC)**
	- Defined: governance docs and code references to `SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT` (`src/shieldcraft/engine.py`, `src/shieldcraft/services/validator/tests_attached_validator.py`).
	- Enforcement: opt-in; tests exercise behavior when env var set (`tests/validator/test_tests_attached_integration.py`).
- **Readiness / Blocking invariants**
	- Defined: `src/shieldcraft/verification/readiness_contract.py`, `docs/governance/VERIFICATION_SPINE.md`.
	- Enforcement: `readiness_evaluator.py` attaches `_readiness` and `_readiness_report` in engine.
	- Tests: `tests/verification/test_readiness_*`.

## Authoritative vs Supporting Docs

- **Authoritative** (govern behavior): `docs/governance/decision_log.md`, `docs/governance/INVARIANTS.md`, `docs/governance/OPERATIONAL_READINESS.md`, `docs/governance/CONTRACTS.md`, `docs/governance/progress.md`, `docs/governance/SE_V1_CLOSED.md`.
- **Supporting** (how-to, examples): `docs/persona/*`, `spec/README.md`, `spec/se_dsl_v1.template.json`.
- **Historical / Phase artifacts**: `docs/archive/*`, `docs/phases/*`.
- **Audit outputs / artifacts**: `artifacts/governance/doc_classification_report.json`, `artifacts/canonicalization/*`, `artifacts/canonical_full_run/*`.

## Known Gaps and Explicit Non-Goals

- **Known gaps** (explicit in `docs/governance/progress.md`): formal progress/state file schema not defined; Phase 14 self-hosting validation failed and remediation is STARTED; specific failing tests classified as spec gaps (bootstrap artifacts, pointer map coverage, generator lockfile contract, checklist normalization).
- **Explicit non-goals**: no feature implementation during foundation-alignment; one-RFC-per-PR and spec-first commit requirements (`docs/pr_structure_phase13.md`).

## Context Anchor v2 (single-screen snapshot)

- **What it is:** Deterministic software manufacturing engine that validates canonical DSL specs and emits auditable, reproducible build artifacts and previews (`spec/`, `src/shieldcraft/engine.py`).
- **Authority:** Canonical DSL/schema (`spec/se_dsl_v1.spec.json`, `spec/schemas/se_dsl_v1.schema.json`) and governance docs (`docs/governance/*`).
- **Current focus:** Verification & Testing Spine (determinism checks, readiness evaluation, TAC gating, self-host validation remediation).
- **Selected facts complete:** canonical DSL/schema present; determinism tooling and regression test present; persona opt-in and non-interference tests present.
- **Selected facts incomplete:** Phase 14 self-hosting validation remediation in progress; formal progress/state file schema OPEN.
- **Use:** Short authoritative snapshot for conversation resets and onboarding; record updates in `docs/governance/decision_log.md`.