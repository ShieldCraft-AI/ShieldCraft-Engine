# RFC Adoption Plan (No-Code / Spec-Only Migration)

This adoption plan proposes an ordered rollout of RFCs, migration steps, and non-goals. Each step is spec-only and does not include code changes.

## Rollout Order (Phase 1 → Phase 4)

1. `rfc-generator-version-contract.md` (Phase 1)
   - Reason: Establish generator lockfile contract early to avoid failing preflight during migration.
   - Spec-only changes: Update schema to require `metadata.generator_version` in production specs; update documentation and linter rules.
   - Migration: Provide `scaffold` tool to add `generator_version` to existing specs; CI flag `--allow-missing-generator-version` for a transition window.

2. `rfc-allowed-checklist-types.md` (Phase 2)
   - Reason: Define canonical `type` set that supports bootstrap and pipeline categories.
   - Spec-only changes: Add `enum` for `type` in `se_dsl_v1.schema.json` and document type semantics.
   - Migration: Introduce CLI linter `validate_types --fix` to map unknown types to `task` with warnings during migration.

3. `rfc-pointer-map-semantics.md` (Phase 3)
   - Reason: Adopt canonical pointer semantics and ensure backward compatibility for pointer_map consumers.
   - Spec-only changes: Add `pointer_map` schema to include both `raw_ptr` and `canonical_ptr`; update pointer auditing contract.
   - Migration: Add `pointer_map_migration` script to canonicalize pointer maps and update test fixtures.

4. `rfc-checklist-pointer-normalization.md` and `rfc-bootstrap-artifacts.md` (Phase 4)
   - Reason: Finalize checklist extraction shape and ensure bootstrap emission invariants with clear spec mapping.
   - Spec-only changes: Update checklist item schema with `requires_code` and `source` metadata; define `bootstrap` classification rules.
   - Migration: Add a compatibility flag to the engine’s preflight to check for missing `source` fields, and provide a transform to map older checklist items to the new shape.

## Spec-only Changes per Step
- Step 1: Update `se_dsl_v1.schema.json` to require `metadata.generator_version` and document the lockfile enforcement policy.
- Step 2: Add an enumerated `type` set in the DSL schema and document type-to-classification mapping. Add `lenient` flag for transitional builds.
- Step 3: Extend `pointer_map.json` schema to include `raw_ptr` and `canonical_ptr`, and define canonical pointer generation rules. Update `manifest` schema for coverage fields.
- Step 4: Define new checklist item fields (`requires_code`, canonical `ptr` usage), and document bootstrap classification mapping (ID presence rule). Update `generator_instructions` guidance and test fixtures.

## Deferred Implementation Notes (No-code)
- Template engine behavior and generated file format remain deferred; this plan addresses only spec-level contract and migration guidance.
- Implementation of engine mapping, linter tools, and compatibility mapping is left to a follow-up implementation PR after RFC acceptance.

## Explicit non-goals
- No code changes or test changes are part of this RFC adoption plan.
- No automatic runtime transformation of pointer maps is part of the plan; we only provide migration scripts and linter recommendations.

## Risks and Mitigations
- Risk: Consumers may rely on old numeric pointer patterns. Mitigation: Provide a `pointer_map_migration` tool and a `raw_ptr` field in pointer_map.json for fallbacks.
- Risk: In-flight specs missing `generator_version`. Mitigation: Provide `--allow-missing-generator-version` for a limited migration window with warnings.

