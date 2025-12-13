## RFC Approval Checklist

This checklist organizes RFCs requiring decisions. Each RFC has explicit yes/no decision questions, blocking dependencies, and approval status.

### RFC: Self-host Bootstrap Artifact Emissions
- Decision question: Should `sections` with `id: "bootstrap"` or `category: "bootstrap"` always cause the self-host pipeline to emit `bootstrap/` outputs and `summary.json`? [Yes/No]
- Blocking dependencies: `rfc-allowed-checklist-types.md` (define bootstrap types), `rfc-generator-version-contract.md` (migration policy)
- Approval status: 
- Approval status: Approved

### RFC: Spec Pointer Map Semantics (IDs vs Indexes)
- Decision question: Adopt id-based pointer canonicalization for arrays with `id` fields and include both `raw_ptr` and `canonical_ptr` in `pointer_map.json`? [Yes/No]
- Blocking dependencies: `rfc-checklist-pointer-normalization.md` (pointer shape needs), pointer toolchain compatibility
- Approval status: 
- Approval status: Approved

### RFC: Generator Lockfile and generator_version Contract
- Decision question: Must `metadata.generator_version` be required in all production specs and strictly match `generators/lockfile.json`? [Yes/No]
- Blocking dependencies: CI and release deployment policy, generator lockfile management
- Approval status: 
- Approval status: Approved

### RFC: Checklist Pointer Normalization & Extraction
- Decision question: Extract scalar leaf nodes and include them as checklist items; include the `requires_code` boolean; use `id`-based pointers where applicable? [Yes/No]
- Blocking dependencies: `rfc-pointer-map-semantics.md` and `rfc-allowed-checklist-types.md`
- Approval status: 
- Approval status: Approved

### RFC: Canonical Allowed Checklist Item Types
- Decision question: Define canonical `type` enums in DSL schema, including `pipeline`, `loader_stage`, `engine_stage`, and others, and adopt `--lenient-types` for migration? [Yes/No]
- Blocking dependencies: release & migration windows, CLI tooling, and linter support
- Approval status: 
- Approval status: Approved

