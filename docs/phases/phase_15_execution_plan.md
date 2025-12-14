# Phase 15 — Self-Hosting Remediation Execution Plan

This plan converts the triaged failures from Phase 14 into a set of actionable remediation PRs. Each remediation PR must implement a single triaged category and follow Phase 15 contract rules.

## Plan Overview
- PRs must implement exactly one of the following categories, in priority order.
- Include spec-first commit where applicable.
- Provide unit tests reproducing the failure, plus regression tests for deterministic self-hosting.

## Failure Categories and Execution Details

1) Generator lockfile / preflight contract
- Authoritative behavior: Preflight returns violations list and `contract_ok` boolean; should not raise exceptions for lockfile mismatches.
- Spec impact: No (contract behavior only) — may require schema clarification/rfc.
- Code areas to modify: `src/shieldcraft/services/generator/contract_verifier.py`, `src/shieldcraft/services/spec/schema_validator.py`, `src/shieldcraft/engine.py` preflight handler.
- Tests to update/add: `tests/test_preflight_contract.py`, `tests/cli/test_validate_spec.py`, new integration tests for lockfile mismatch.
- Backward-compatibility guard: No change in behavior for CLI (error on strict mode only) — provide test guard for lenient mode.
- PR order: 1

2) DSL version enforcement and mapping
- Authoritative behavior: Engine accepts `metadata.spec_format` and loader maps it to canonical `dsl_version`; Engine uses loader's resolved `dsl_version` to validate.
- Spec impact: Yes (clarify/specify mapping in schema); create RFC patch if necessary.
- Code areas: `src/shieldcraft/dsl/loader.py`, `src/shieldcraft/engine.py`, `src/shieldcraft/dsl/schema/*`.
- Tests: Update `tests/test_engine.py`, `tests/engine/test_engine_end_to_end.py`, and spec fixtures in `spec/se_dsl_v1.spec.json`.
- Backward-compatibility guard: No (canonical mapping required), provide a migration note.
- PR order: 2

3) EvidenceBundle API compatibility
- Authoritative behavior: `EvidenceBundle.build()` accepts optional `invariants` and `graph` (default empty lists) to remain compatible with existing callers.
- Spec impact: No (governance behavior; RFC if API change is desired formally).
- Code areas: `src/shieldcraft/services/governance/evidence.py`, `src/shieldcraft/engine.py` (call sites).
- Tests: `tests/test_governance_evidence.py`, engine evidence generation tests, and self-host generation tests.
- Backward-compatibility guard: Yes (default params preserve compatibility).
- PR order: 3

4) CodeGenerator output shape standardization
- Authoritative behavior: CodeGenerator returns canonical dict with `outputs` list and `codegen_bundle_hash`. Writers and engine must expect and adapt.
- Spec impact: No (implementation behavior), optionally document the canonical output shape.
- Code areas: `src/shieldcraft/services/codegen/generator.py`, `src/shieldcraft/engine.py`, `src/shieldcraft/services/codegen/emitter/writer.py`
- Tests: `tests/test_codegen_engine.py`, emitter tests and collateral engine tests.
- Backward-compatibility guard: Yes (adapter layer in generator or engine to accept both formats until enforcement PR merges).
- PR order: 4

5) Pointer map canonicalization
- Authoritative behavior: Pointer map entries must include `canonical_ptr` or exclusively use canonical id-based pointers; loader/AST builder resolves canonicals accordingly.
- Spec impact: Yes (pointer_map schema update). RFC required if not already approved.
- Code areas: `spec/pointer_map.json`, `src/shieldcraft/services/ast/builder.py`, pointer auditor `src/shieldcraft/services/spec/pointer_auditor.py`
- Tests: `tests/spec/test_pointer_map.py`, `tests/spec/test_pointer_locality.py`.
- Backward-compatibility guard: Yes (raw+canonical fields or a migration flag `SHIELDCRAFT_PTRMAP_LEGACY` to accept numeric index pointers).
- PR order: 5

6) Pointer coverage report shape
- Authoritative behavior: `ensure_full_pointer_coverage` returns {total_pointers, ok_count, missing_count, ok[], missing[]}.
- Spec impact: No (reporting format only; document in helper API).
- Code areas: `src/shieldcraft/services/spec/pointer_auditor.py`, `src/shieldcraft/services/spec/schema_validator.py` if needed.
- Tests: `tests/spec/test_pointer_missing.py`
- Backward-compatibility guard: No; add adapter shim returning older shape while deprecating.
- PR order: 6

7) Checklist ID canonicalization
- Authoritative behavior: Checklist item `id` should be canonical stable 8-char hash by default; legacy `TASK-####` accepted only under migration flag.
- Spec impact: No (spec clarifies canonical id generation); may require RFC for canonical ID format.
- Code areas: `src/shieldcraft/services/checklist/idgen.py`, `src/shieldcraft/services/checklist/generator.py`.
- Tests: `tests/test_checklist.py`, `tests/test_task_id_and_category.py` and checklist integration tests.
- Backward-compatibility guard: Yes (`SHIELDCRAFT_LENIENT_TYPES` or another migration guard).
- PR order: 7

8) JSON canonical formatting
- Authoritative behavior: Spec files must be serialized canonical JSON: `ensure_ascii=False`, `sort_keys=True`, `indent=2` to align with canonicalizer.
- Spec impact: Yes; update guidelines and add pre-commit/pipeline test.
- Code areas: Re-serialize `spec/*.json` files, `src/shieldcraft/services/spec/schema_validator.py` for enforcement.
- Tests: `tests/spec/test_format_check.py` and CI check.
- Backward-compatibility guard: No — deterministic formatting required; update repo with canonical forms.
- PR order: 8

9) Cross-section return type enforcement
- Authoritative behavior: `cross_section_checks` returns list of dicts with `ptr` fields (never a string or primitive direct type).
- Spec impact: No (behavior change implemented in code).
- Code areas: `src/shieldcraft/services/checklist/cross.py`, `src/shieldcraft/services/checklist/extractor.py`.
- Tests: `tests/test_deps_and_cross.py::test_cross_section_missing_arch` and adjunct tests.
- Backward-compatibility guard: No; ensure adapter for older primitive outputs remains for a single release if necessary.
- PR order: 9

10) Self-host manifest summary completeness
- Authoritative behavior: `run_self_host` writes a deterministic `summary.json` even on validation failures (status: failure + error details), and manifest fields are deterministic.
- Spec impact: No (emission behavior), but may require a small schema clarification to document required fields even on failure.
- Code areas: `src/shieldcraft/main.py`, `src/shieldcraft/engine.py`, `src/shieldcraft/dsl/schema/manifest.schema.json`
- Tests: `tests/selfhost/test_selfhost_minimal.py`, `tests/selfhost/test_bootstrap_codegen.py` and self-host pipeline integration tests.
- Backward-compatibility guard: No; deterministic summary generation is desired for CI reliability.
- PR order: 10

## PR Validation Steps
- Each PR must include unit tests reproducing the failing case and a deterministic self-host run verification step.
- CI must run the full pytest -q and the deterministic self-host twice and validate identical artifacts.

## Acceptance Criteria (for each PR)
- All tests for modified areas pass in local runs and CI.
- Deterministic validation passes for the self-host run where applicable.
- Changes documented and, if spec changes are required, spec-first commit and RFC reference included.

## Handoff
- Merge PRs into a `phase15/remediation` branch and re-run Phase 14 validation on merge to confirm the full suite and deterministic self-hosting pass.

