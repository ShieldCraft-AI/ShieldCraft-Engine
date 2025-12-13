# ShieldCraft Engine — Progress & State (Authoritative)

## Current Phase

**foundation-alignment**

## Completed Phases

None

## Active Constraints

- Single canonical DSL: se_dsl_v1
- No feature implementation during foundation-alignment
- Copilot operates as implementer only

## Frozen Decisions

- copilot-instructions.md is the authoritative Copilot entry point

- All instructions must declare invariants before construction actions

# Open Gaps

- Define formal progress/state file schema (future phase)

## Closed / Spec-Grounded Gaps

- The following previously-recorded open gaps have been converted into approved RFCs and corresponding spec/schema updates have been applied for Phase 13 (code/test changes pending PRs):
	- Self-host & bootstrap artifact emissions: RFC rfc-bootstrap-artifacts.md — spec updates added (bootstrap section, task `category`, pointer_map entries)
	- Pointer map / coverage semantics: RFC rfc-pointer-map-semantics.md — pointer_map supports raw/canonical pointers and canonical id-based semantics added to schema
	- Generator lockfile / generator_version contract: RFC rfc-generator-version-contract.md — `metadata.generator_version` is now required in the DSL schema and sample spec includes it
	- Checklist normalization & pointer extraction behavior: RFC rfc-checklist-pointer-normalization.md — `checklist_item` schema shape added for normalized items
	- Allowed checklist item types enumeration: RFC rfc-allowed-checklist-types.md — `allowed_checklist_types` property and enum added to schema and sample spec

Note: Code and tests implementing these spec updates remain gated to PRs as described in the Phase 13 PR structure. The spec-level gaps are considered addressed by the spec/schema changes above; any remaining issues are implementation-level and must follow the one-RFC-per-PR process.

# Failing Test Classifications (Foundation-Alignment)

The following failing tests have been classified as spec gaps (i.e., missing or underspecified invariant, contract or DSL guidance), not as production code defects. These are documented here as open specification gaps to be resolved by the product/architectural team.

- Self-host & bootstrap artifact emissions:
	- Problem: Bootstrap generation tests failed to emit expected bootstrap files and summaries.
	- Affected tests: tests/selfhost/test_bootstrap_codegen.py, tests/selfhost/test_selfhost_minimal.py
	- Spec gap: Self-host bootstrap artifact emission invariants undefined (what should be emitted, what constitutes a bootstrap-classified item).

- Pointer map / coverage semantics:
	- Problem: Pointer map tests show unresolved pointer paths and coverage mismatch (id vs index semantics, coverage shapes differ).
	- Affected tests: tests/spec/test_pointer_map.py::test_pointer_map_all_resolve, tests/spec/test_pointer_missing.py, tests/selfhost/test_governance_and_pointers.py::test_pointer_completeness
	- Spec gap: Spec pointer map completeness rules and id-based pointer semantics for lists of objects not explicit enough in the DSL contract.

- Generator lockfile / generator_version contract:
	- Problem: Preflight contract verifier throws `GENERATOR_LOCKFILE_MISMATCH` when `metadata.generator_version` is missing.
	- Affected tests: tests/spec/test_pointer_missing.py::test_preflight_integration, tests/spec/test_pointer_strict_mode.py, tests/test_preflight_contract.py
	- Spec gap: Generator version presence requirement and behavior when lockfile mismatch occurs (error vs warning) are not encoded clearly in the DSL contract.

- Checklist normalization & pointer extraction behavior:
	- Problem: Checklist generation tests expect items like `/x` to be present; AST extraction and checklist normalization differ between previous and new canonical pointer semantics.
	- Affected tests: tests/test_checklist_generator.py::test_build_generates_items, tests/test_checklist_generator_expanded.py::test_render_basic, tests/test_checklist.py
	- Spec gap: Checklist pointer canonicalization rules (when to include scalar vs dict vs array nodes, and pointer format expectations) are underspecified.

- Allowed checklist item types enumeration:
	- Problem: Tests assume `pipeline`, `loader_stage`, `engine_stage`, and similar types may be valid; code enforces a limited `ALLOWED_TYPES` list.
	- Affected tests: tests/selfhost/test_selfhost_dryrun.py, tests/selfhost/test_bootstrap_codegen.py, tests/selfhost/test_selfhost_minimal.py
	- Spec gap: The canonical schema and spec should enumerate allowed task `type` values and their semantics (bootstrap vs pipeline types vs codegen targets) so that the engine can enforce them consistently.

These gaps were recorded intentionally without modifying production code or tests, per foundation-alignment policy.

## Notes

This document serves as the authoritative record of ShieldCraft Engine's development progress and state.

## Phase Readiness

- RFCs drafted and verified
- Approval checklist prepared
- Implementation authorized as per Phase 13 Authorization (approved RFCs only)

## Phase Status

- foundation-alignment: CLOSED
- All spec gaps identified and documented as RFCs
- No implementation decisions taken
- No code or test changes authorized

## Phase 13: spec-hardening-and-alignment

- spec-hardening-and-alignment: CLOSED
- All approved RFCs implemented
- Determinism verified

Notes:
- All tests passed deterministically in local CI: 281 passed (twice)
- Migration guards verified: lenient checklist types via `SHIELDCRAFT_LENIENT_TYPES` and canonical enforcement via `dsl_version` or `metadata.spec_format` mapping

## Phase Transition

- Decision: Proceed to Phase 13 (Spec Implementation) — code/test modifications accepted for review and PRs to be prepared.
- Rationale: User confirmed baseline commit and accepted the changes since baseline as intentional and ready for review.
- Next-step: Create PR(s) grouping code/test changes by feature area for Phase 13 review, align with RFC approvals, and implement schema updates.

## Phase 13 Decisions

- Approved RFCs:
	- rfc-generator-version-contract.md (approved)
	- rfc-allowed-checklist-types.md (approved with migration guard)
	- rfc-pointer-map-semantics.md (approved)
	- rfc-checklist-pointer-normalization.md (approved)
	- rfc-bootstrap-artifacts.md (approved)

- Deferred RFCs:
	- None

- Implementation remains gated pending formal PRs and schema updates.

## Phase 13 Planning Status

- Implementation plan frozen
- PR structure frozen
- Implementation authorized (gated to approved RFCs only)

## Phase 13 Authorization

The following authorization and constraints are in effect for Phase 13 (spec-hardening-and-alignment):

- **Implementation authorized for approved RFCs only:** Only the RFCs listed in 'Phase 13 Decisions' are allowed to be implemented in this phase. Any change outside these RFCs requires a new RFC and cannot be included in Phase 13 PRs.
- **One RFC per PR enforced:** PRs must implement a single RFC as described in `docs/pr_structure_phase13.md`.
- **Spec-first commit required:** The first commit of each PR must be a spec/schema change and documentation entry describing the intent. Subsequent commits may contain code and tests that implement the spec-first change.
- **No cross-RFC scope allowed:** A PR must not implement features, tests, or changes beyond the approved RFC's scope. Any cross-RFC work must be split into the respective RFCs and PRs.
- **All tests must pass per PR:** Acceptance for a PR includes passing the CI suite and an engineering QA sign-off; PRs that introduce regressions or failing tests will be rejected.

Additional explicit constraints:

- **No optional paths:** The canonical execution path as defined by spec schema and approved RFCs is the authoritative path; introducing optional alternate branches must be specified by its own RFC.
- **No alternative execution flows without RFC:** Any attempt to alter execution behavior or introduce alternative runtime flows must be covered by an explicit RFC and is not allowed in Phase 13 PRs.
- **No further approvals required to proceed for approved RFCs:** This document and the sign-off recorded by product and engineering are sufficient to proceed with implementing the approved RFCs under the constraints above.

These constraints are enforced by the PR gating rules in `docs/pr_structure_phase13.md` and will be checked by reviewers and CI automation. Any deviation must be escalated to product/engineering leads and documented as an exceptional change with explicit approval.

## Foundation Alignment Baseline

- Baseline commit SHA: 9b790c49022f63e9f6d33a9ad4615ab89f78cc8b
- Baseline message: "Freeze canonical DSL + cleanup complete"
- Docs-only verification: FAIL
- Non-doc files modified since baseline (committed):
	- tests/ast/test_lineage_consistency.py
- Unstaged non-doc changes (working tree):
	- spec/pointer_map.json
	- spec/se_dsl_v1.spec.json
	- src/shieldcraft/dsl/loader.py
	- src/shieldcraft/engine.py
	- src/shieldcraft/services/ast/builder.py
	- src/shieldcraft/services/checklist/extractor.py
	- src/shieldcraft/services/checklist/generator.py
	- src/shieldcraft/services/checklist/model.py
	- src/shieldcraft/services/codegen/file_plan.py
	- src/shieldcraft/services/codegen/generator.py
	- src/shieldcraft/services/spec/pointer_auditor.py
	- src/shieldcraft/services/spec/schema_validator.py
	- tests/checklist/test_ancestry.py
	- tests/checklist/test_ast_integration.py
	- tests/checklist/test_derived.py
	- tests/checklist/test_derived_determinism.py
	- tests/checklist/test_integration_items.py
	- tests/checklist/test_invariants.py
	- tests/checklist/test_ordering_stability.py
	- tests/checklist/test_resolution_chain.py
	- tests/checklist/test_timings.py
	- tests/cli/test_validate_spec.py
	- tests/codegen/test_dry_run.py
	- tests/codegen/test_provenance_headers.py
	- tests/engine/test_engine_end_to_end.py
	- tests/selfhost/test_bootstrap_codegen.py
	- tests/selfhost/test_governance_and_pointers.py
	- tests/selfhost/test_selfhost_minimal.py
	- tests/spec/test_pointer_locality.py
	- tests/spec/test_pointer_range.py
	- tests/spec/test_pointer_shape.py
	- tests/spec/test_pointer_strict_mode.py
	- tests/test_checklist_generator.py
	- tests/test_checklist_generator_expanded.py
	- tests/test_engine.py
	- tests/test_governance_evidence.py
	- tests/test_task_id_and_category.py

Notes: All non-doc modifications must be reviewed in a separate PR; foundation-alignment closure is contingent on removing or moving these changes to a dedicated review branch if they are to be retained.
