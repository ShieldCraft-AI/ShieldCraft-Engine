# Implementation Plan for Approved RFCs (Phase 13 - Spec Implementation)

This plan maps each approved RFC to specific spec, code, and test files that will be impacted. Implementation is blocked until PRs are created referencing these RFCs; these are the suggested changes for structured implementation only.

## rfc-generator-version-contract.md
- Spec files to change:
  - spec/schemas/se_dsl_v1.schema.json (add `metadata.generator_version` required field)
  - spec/generators/lockfile.json (lockfile coverage docs)
- Code areas impacted (paths only):
  - src/shieldcraft/services/generator/contract_verifier.py
  - src/shieldcraft/services/preflight/preflight.py
  - src/shieldcraft/engine.py (preflight invocation and error handling)
- Test areas impacted (paths only):
  - tests/spec/test_pointer_missing.py
  - tests/test_preflight_contract.py
  - tests/selfhost/test_selfhost_dryrun.py
- Migration requirements: YES — CLI linter and migration scaffolding to add `metadata.generator_version` to existing specs.
- Backward-compatibility guard requirements: CLI flag `--allow-missing-generator-version` for a transition window.
- PR dependency order: Must be first (PR-1), since many tests and preflight checks depend on generator_version presence.

## rfc-allowed-checklist-types.md
- Spec files to change:
  - spec/schemas/se_dsl_v1.schema.json (type enum for checklist items)
  - spec/pointer_map.json and any sample specs referencing types
- Code areas impacted (paths only):
  - src/shieldcraft/services/checklist/model.py (ALLOWED_TYPES, classification)
  - src/shieldcraft/services/checklist/generator.py (classification and derived tasks)
  - src/shieldcraft/services/checklist/derived.py (derived task types mapping)
- Test areas impacted (paths only):
  - tests/selfhost/test_selfhost_dryrun.py
  - tests/selfhost/test_bootstrap_codegen.py
  - tests/test_checklist_generator.py
- Migration requirements: YES — linter to suggest mapping and `--lenient-types` flags.
- Backward-compatibility guard requirements: Linter+routines; default unknown -> `task` only during lenient migration.
- PR dependency order: PR-2 (after lockfile PR-1 for safe preflight expectations).

## rfc-pointer-map-semantics.md
- Spec files to change:
  - spec/pointer_map.json (add `canonical_ptr`) and pointer_map schema updates in spec/schemas
  - spec/schemas/manifest.schema.json (coverage outputs format)
- Code areas impacted (paths only):
  - src/shieldcraft/services/ast/builder.py (pointer segment canonicalization docs)
  - src/shieldcraft/services/spec/pointer_auditor.py
  - src/shieldcraft/dsl/loader.py (extract_json_pointers)
- Test areas impacted (paths only):
  - tests/spec/test_pointer_map.py
  - tests/spec/test_pointer_missing.py
  - tests/selfhost/test_governance_and_pointers.py
- Migration requirements: YES — Provide pointer_map_migration script to dual-emit `raw_ptr` and `canonical_ptr`.
- Backward-compatibility guard requirements: Pointer_map schema must include `raw_ptr`; consumers must fallback to `raw_ptr` when `canonical_ptr` is missing.
- PR dependency order: PR-3 (after PR-1 and PR-2 recommended but not strictly required).

## rfc-checklist-pointer-normalization.md
- Spec files to change:
  - spec/schemas/se_dsl_v1.schema.json (checklist item schema: add `requires_code`, `source_pointer`, `source_section` fields)
  - spec/pointer_map.json (ensure mapping includes scalar node coverage)
- Code areas impacted (paths only):
  - src/shieldcraft/services/checklist/extractor.py
  - src/shieldcraft/services/checklist/generator.py (extraction and normalization)
  - src/shieldcraft/services/checklist/model.py (normalize_item expectations)
- Test areas impacted (paths only):
  - tests/test_checklist_generator.py
  - tests/test_checklist_generator_expanded.py
  - tests/test_checklist.py
- Migration requirements: YES — reserialize checklist for existing specs to include `source_pointer` and scalar leaves.
- Backward-compatibility guard requirements: Linter for mapping old pointer locations; `pointer_map` must provide `raw_ptr` fallback.
- PR dependency order: PR-4 (after PR-3 pointer_map semantics and PR-2 allowed types).

## rfc-bootstrap-artifacts.md
- Spec files to change:
  - spec/schemas/se_dsl_v1.schema.json (define `bootstrap` classification rules in `sections` schema)
  - spec/examples/selfhost/bootstrap_spec.json updates
- Code areas impacted (paths only):
  - src/shieldcraft/services/codegen/generator.py (bootstrap codegen path handling)
  - src/shieldcraft/engine.py (self-host run outputs and manifest creation)
- Test areas impacted (paths only):
  - tests/selfhost/test_bootstrap_codegen.py
  - tests/selfhost/test_selfhost_minimal.py
- Migration requirements: NO (enforce new behavior on new specs), but optional migration for existing bootstrap tasks to add `category: "bootstrap"`.
- Backward-compatibility guard requirements: If a spec doesn't have `category: bootstrap` or `id`, emission remains optional or requires explicit `bootstrap: true` flag.
- PR dependency order: PR-5 (after PR-1, PR-2, PR-3, PR-4 since it relies on pointer semantics and allowed types).

## PR dependency summary
- PR-1: rfc-generator-version-contract.md (lockfile, generator_version) — prerequisite for others.
- PR-2: rfc-allowed-checklist-types.md (type enum) — needed before normalization.
- PR-3: rfc-pointer-map-semantics.md (pointer_map canonicalization) — supports pointer mapping for checklist and bootstrap.
- PR-4: rfc-checklist-pointer-normalization.md (checklist extraction) — relies on PR-2 and PR-3.
- PR-5: rfc-bootstrap-artifacts.md (bootstrap emission) — relies on all prior PRs.

Note: This is a spec-level implementation plan and PR skeleton. Actual PRs should include schema patches, migration scripts, sample spec changes for tests, and clear migration instructions. No code changes are authorized within Phase 13 planning without separate PR review.

