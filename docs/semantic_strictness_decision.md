Decision: Default Semantic Strictness Level

Date: 2025-12-15

Summary:
- We enable SEMANTIC_STRICTNESS_LEVEL_1 by default to improve early detection of malformed or incomplete DSL specifications.
- Level 1 enforces that `sections` is a non-empty array.

Rationale:
- `sections` is required by the DSL schema and its absence/emptiness leads to ambiguous checklist/plan generation.
- Enabling Level 1 provides meaningful correctness without requiring full semantic mapping.

Backward compatibility:
- Default behavior can be disabled with `SEMANTIC_STRICTNESS_DISABLED=1` to preserve older workflows.
- Higher levels remain opt-in via `SEMANTIC_STRICTNESS_LEVEL_N=1` environment flags.

Auditing:
- The engine attaches `semantic_strictness_policy` to `summary.json` and `manifest` for explainability.
- Validation errors include deterministic codes and JSON Pointer locations.
