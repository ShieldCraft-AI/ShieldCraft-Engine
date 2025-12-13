# Foundation-Alignment Handoff Summary

What is locked:
- Pointer canonicalization rules favor id-based pointer segments in arrays when `id` fields are present.
- DSL must enforce `metadata.generator_version`; preflight will validate lockfile matches.
- Checklist extraction will include scalar leaf nodes and `requires_code` in canonical items.
- RFCs drafted for: bootstrap artifact behavior, pointer semantics, generator-version contract, checklist item normalization, allowed checklist types.

What is explicitly undecided:
- The exact `type` enumerations for checklist items and the mapping to codegen templates.
- Detailed migration timing (transition windows) for pointer_map canonicalization.
- How strict the generator lockfile enforcement should be (strict vs. tolerance levels for semver).

Approved artifacts:
- RFC documents in `docs/rfc/`:
  - rfc-bootstrap-artifacts.md
  - rfc-pointer-map-semantics.md
  - rfc-generator-version-contract.md
  - rfc-checklist-pointer-normalization.md
  - rfc-allowed-checklist-types.md
- Approval checklist: `docs/rfc/approval_checklist.md`
- Adoption plan: `docs/rfc/adoption_plan.md`
- Instruction template and invariants: `docs/se_instruction_template_v1.json`, `docs/se_instruction_invariants_v1.md`

Explicit non-goals:
- No code or tests will be changed in this phase (foundation-alignment). All changes are in documentation and RFCs.
- No automatic migration tooling will be merged; only spec and linter recommendations are provided.

Required inputs for the next phase (Phase 13 - Spec Implementation):
- Approval decisions for the RFCs above (Y/N per checklist). If N, provide issue describing required changes.
- Updated canonical DSL schema to reflect approved choices (e.g., `type` enum, pointer_map `canonical_ptr` vs `raw_ptr`).
- Migration plan for pointer_map and generated artifact compatibility.
- CI/lint updates and CLI flags for lenient migration (if any).

Notes:
- Current working tree includes uncommitted code/test changes from previous tasks in this session; those are out of scope for Phase 12 (foundation-alignment) closure and must be reviewed via separate change-control (PR) if they are to be retained.

