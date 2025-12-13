# Phase 14 Self-Hosting Validation — Failure Triage

This file categorizes the failures observed during Phase 14 validation runs and maps them to root causes and RFC alignment. This is a frozen triage artifact — no fixes were applied in Phase 14; this document is authoritative for the classification of defects requiring targeted PRs.

---

## Summary of Test Run
- Total passing tests: 224
- Total failing tests: 55
- Date: 2025-12-13
- Reproduction: `pytest -q` after self-host runs; artifacts saved in `artifacts/self_hosting_run_1` and `_run_2`.

---

## Failure Categories and Details

1) Generator lockfile / preflight contract
- Observed error: `ValueError: GENERATOR_LOCKFILE_MISMATCH: expected 1.0.0 but spec requests unknown`
- Affected tests (examples):
  - tests/checklist/test_ast_integration.py::test_ast_integration_basic
  - tests/checklist/test_timings.py::test_timings_exist
  - tests/test_preflight_contract.py::test_preflight_basic
  - tests/cli/test_validate_spec.py::test_validate_spec_valid_spec
- Affected files: `src/shieldcraft/services/generator/contract_verifier.py`, `generators/lockfile.json`.
- Root cause summary: Current implementation raises a ValueError when the spec omits `metadata.generator_version` and a `generators/lockfile.json` is present. Tests and preflight should receive violation objects not thrown exceptions.
- RFC alignment: `rfc-generator-version-contract.md`
- Required behavior (authoritative): Preflight should return a violations list and mark contract_ok=False for mismatch; raising an exception is reserved for CI or CLI enforcement, not unit-level contract checks.
- Implementation notes (non-executable): Adjust `verify_generation_contract` to return violations; update preflight to aggregate violations rather than raising.

2) DSL version enforcement
- Observed error: `ValueError: DSL version check failed: expected 'canonical_v1_frozen', got 'None'. Spec must use frozen canonical DSL.`
- Affected tests (examples): tests/test_engine.py::test_engine_pipeline, tests/engine/test_engine_end_to_end.py::test_engine_end_to_end_basic
- Affected files: `src/shieldcraft/engine.py`, `src/shieldcraft/dsl/loader.py`
- Root cause summary: Engine enforces `dsl_version` strictly; many tests generate specs with `metadata.spec_format` instead and expect loader mapping to canonical DSL (`spec_format` => `dsl_version`).
- RFC alignment: `rfc-pointer-map-semantics.md` and the Phase 13 schema changes that map `metadata.spec_format` to canonical DSL v1.
- Required behavior: Engine must accept `metadata.spec_format` and map without raising, or tests must include explicit `dsl_version` for canonical specs.
- Implementation notes: Add mapping in engine `run` checks to accept `metadata.spec_format` values or move mapping into loader and ensure engine uses loader result to decide validation.

3) EvidenceBundle backward compatibility
- Observed error: `TypeError: EvidenceBundle.build() missing 2 required keyword-only arguments: 'invariants' and 'graph'`
- Affected tests: tests/test_governance_evidence.py::test_evidence, engine path when generating evidence
- Affected files: `src/shieldcraft/services/governance/evidence.py`, `src/shieldcraft/engine.py` (call sites)
- Root cause summary: New EvidenceBundle signature requires (checklist, invariants, graph, provenance); some calls in tests and code only pass a subset leading to TypeError.
- RFC alignment: `rfc-bootstrap-artifacts.md` and governance invariants updates.
- Required behavior: EvidenceBundle.build should accept optional invariants/graph (default to []), and the engine should provide invariants/graph when available.
- Implementation notes: Make `invariants` and `graph` optional with default empty lists to protect legacy callers.

4) Checklist ID canonicalization
- Observed error: Assertion expecting 8-char stable ID but sees 'TASK-0001' (9 chars);
- Affected tests: tests/test_checklist.py::test_checklist; tests/test_task_id_and_category.py::test_stable_ids
- Affected files: `src/shieldcraft/services/checklist/idgen.py`, `src/shieldcraft/services/checklist/generator.py`
- Root cause summary: The generator sometimes uses legacy 'TASK-####' IDs in generated items instead of the canonical `stable_id` 8-char hash.
- RFC alignment: `rfc-checklist-pointer-normalization.md` and `rfc-allowed-checklist-types.md` for migration guidance.
- Required behavior: Default item id generation should use deterministic `stable_id(ptr, text)[0:8]` for canonical specs; legacy 'TASK-####' can be maintained under a migration flag.
- Implementation notes: Replace fallback id generator in `ChecklistGenerator` with `stable_id()` and ensure tests expect 8-char IDs or adapt tests to `stable_id()`.

5) CodeGenerator output shape
- Observed error: KeyError or other callers expecting outputs format mismatches (KeyError: 0 when content indexed)
- Affected tests: tests/test_codegen_engine.py::test_codegen_outputs, several engine paths
- Affected files: `src/shieldcraft/services/codegen/generator.py`, `src/shieldcraft/engine.py`, `src/shieldcraft/services/codegen/emitter/writer.py`
- Root cause summary: CodeGenerator.run returns variable shapes (list vs dict with `outputs`) and callers do not handle all shapes; Writer expects list of dicts.
- RFC alignment: `rfc-bootstrap-artifacts.md` and implementation patterns for codegen outputs.
- Required behavior: `CodeGenerator.run` must return canonical dict with `outputs`: list and `codegen_bundle_hash` and engine/writer must expect this shape.
- Implementation notes: Unify output shape and add adapter layers for backward compatibility.

6) Pointer map semantics (canonical id vs index)
- Observed error: `Pointer mismatches: [ ... ]` where pointer map values are numeric indices while spec uses canonical id-based pointers
- Affected tests: tests/spec/test_pointer_map.py::test_pointer_map_values_match_task_ptrs
- Affected files: `spec/pointer_map.json`, `src/shieldcraft/services/ast/builder.py`
- Root cause summary: Pointer map uses `/sections/1/tasks/0` index-based pointers while AST and spec use `/sections/ast_construction/tasks/0` (ID-based segment). Canonical pointer semantics changed; pointer_map must be canonical or provide both `raw_ptr` and `canonical_ptr`.
- RFC alignment: `rfc-pointer-map-semantics.md` and Phase 13 pointer map canonicalization.
- Required behavior: `spec/pointer_map.json` must provide `canonical_ptr` fields or use canonical id-based pointers; or provide both raw + canonical for backward compatibility.
- Implementation notes: Update pointer_map entries to include `canonical_ptr` aligned with AST, or reserialize `pointer_map.json` to canonical format.

7) Pointer coverage report shape
- Observed error: Coverage report keys missing (test expects `total_pointers`, `ok_count`, `missing_count` but got `count` struct).
- Affected tests: tests/spec/test_pointer_missing.py
- Affected code: src/shieldcraft/services/spec/pointer_auditor.py
- Root cause summary: `ensure_full_pointer_coverage` returns a hybrid shape (count dict and missing/ok lists) not the explicit key set expected by tests.
- RFC alignment: `rfc-pointer-map-semantics.md` details required manifest coverage fields.
- Required behavior: Return dict with `total_pointers`, `ok_count`, `missing_count`, `ok`, `missing` for backward compatibility and clarity.
- Implementation notes: Provide wrapper or convert return shape to match test expectations.

8) JSON canonical formatting (unicode vs \uXXXX escapes)
- Observed error: Re-serialized JSON differs on unicode arrow char vs escaped unicode sequence (`\u2192` vs `→`) and thus fails formatting deterministic check.
- Affected tests: tests/spec/test_format_check.py::test_json_formatting_deterministic
- Affected files: `spec/se_dsl_v1.spec.json`, `spec/pointer_map.json` etc.
- Root cause summary: Original JSON uses unicode escaped sequences; canonicalization uses `ensure_ascii=False` producing direct unicode characters.
- RFC alignment: Phase 13 spec formatting canonicalization and `determinism` policy.
- Required behavior: Spec files should be canonicalized with `ensure_ascii=False`, `sort_keys=True`, `indent=2` and saved accordingly in repo.
- Implementation notes: Re-serialize relavent spec files and add a pre-commit to enforce canonical formatting.

9) Cross-section return type mismatch
- Observed error: TypeError: string indices must be integers, not 'str' in `tests/test_deps_and_cross.py` pointing to `cross_section_checks` returning string instead of list/dict
- Affected tests: tests/test_deps_and_cross.py::test_cross_section_missing_arch
- Affected file: `src/shieldcraft/services/checklist/cross.py`
- Root cause summary: Function returned a string in some code path (or out-of-spec data type) rather than a list/dict list.
- RFC alignment: `rfc-checklist-pointer-normalization.md` and `rfc-pointer-map-semantics.md` may affect this behavior
- Required behavior: `cross_section_checks` must return a list of dict objects each with `ptr` fields.
- Implementation notes: Tighten return types; add unit tests to validate types; ensure all code paths return list/dict.

10) Self-host manifest completeness & summary missing
- Observed error: `.selfhost_outputs/summary.json` missing (schema validation failing earlier led to no summary being created), then manifest missing fields; summary/manifests created only on success.
- Affected tests: tests/selfhost/test_selfhost_minimal.py::test_selfhost_minimal_pipeline, other selfhost tests
- Affected files: `src/shieldcraft/main.py`, `src/shieldcraft/engine.py` (manifest building), `src/shieldcraft/dsl/schema/manifest.schema.json`
- Root cause summary: Schema validation fails for spec that uses `spec_format` mapping or missing `dsl_version`, leading to early exit without summary; subsequent tests expect summary presence.
- RFC alignment: `rfc-bootstrap-artifacts.md`, `rfc-generator-version-contract.md`
- Required behavior: For self-host runs, validation errors should be surfaced in `errors.json` and `summary.json` should exist (with status failure) for consistent CI handling; manifest schema fields required for determinism should be present or absent deterministically.
- Implementation notes: Ensure `run_self_host` writes a deterministic `summary.json` even on validation failures (status: failure + details) and manifest incomplete fields still filled deterministically.

---

## Actions for Triaged Items
- Each category should be handled as a focused PR aligned with the relevant RFC or as a compatibility PR where RFC exists.
- Priority ordering (recommended):
  1. Generator lockfile contract behavior
  2. Engine/DSL mapping (`spec_format` mapping)
  3. EvidenceBundle backward compatibility
  4. Codegen output shape standardization
  5. Pointer map canonicalization
  6. Pointer coverage shape
  7. Checklist ID canonicalization
  8. JSON canonical formatting
  9. Cross-section type enforcement
  10. Self-host summary completeness

## Traceability
- All categories reference RFCs where relevant and require spec-first changes if they affect the canonical DSL.
- Implementation notes above are non-executable and intended to be used for PR guidance.

---

## Authors
- Copilot (automation-assisted triage)
- Validated by present test run logs (pytest captured output) — see artifacts in `artifacts/self_hosting_run_1` and `/tmp/pytest_full_run.txt`.

---

Status: FROZEN — This triage document is authoritative for Phase 14 failure classifications. No fixes in this phase.
