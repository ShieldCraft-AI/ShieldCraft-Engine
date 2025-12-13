# RFC: Canonical Allowed Checklist Item Types

Problem statement (linked tests):
- Failing tests: [tests/selfhost/test_selfhost_dryrun.py](tests/selfhost/test_selfhost_dryrun.py), [tests/selfhost/test_bootstrap_codegen.py](tests/selfhost/test_bootstrap_codegen.py)
- Summary: Tests and product needs reference `pipeline`, `loader_stage`, `engine_stage`, and other specialized task `type`s, but `ChecklistModel.ALLOWED_TYPES` enforces a restricted set (e.g., `module`, `task`, `fix-dependency`, etc.) in code; any mismatch causes blocking normalization failures in the generator. The allowed types need to be canonicalized in the DSL spec.

Current observed behavior:
- Engine throws `ValueError: Item type 'pipeline' not in allowed set` when items carry non-allowed `type`; this causes preflight or build failure in self-host mode.

Proposed canonical rule:
- The DSL must list a canonical set of allowed checklist item `type` values and their classification semantics:
  - Core items (task, module, integration, fix-dependency, resolve-invariant, resolve-cycle, etc.)
  - Bootstrap-related: `loader_stage`, `engine_stage`, `test_stage`, `bootstrap_impl`
  - Pipeline-level: `pipeline`, `engine`, `service` (if needed)
  - Derived tasks: `module_test`, `module_imports`, `module_init`
- The canonical list will be the authority for normalization and validate operations; engine `ALLOWED_TYPES` must strictly conform to the specified set.

Explicit invariants:
- Invariant: The canonical DSL `se_dsl_v1.schema.json` must enumerate allowed `type` values for checklist items and categorize them into `bootstrap`, `pipeline`, `codegen`, or `governance` groups.
- Invariant: The engine must validate `item['type']` against the canonical list and map unknown values to `task` by default only under controlled migration with a linter.

Backward-compatibility notes:
- For backward compatibility with older specs: When an unknown `type` value is encountered, the engine should either: (A) emit a warning and treat as `task`, or (B) fail the build if strict mode is enabled. The CLI should support a `--lenient-types` flag to ease migration.

Out-of-scope items:
- The precise mapping of each `type` to codegen templates—the RFC focuses on allowed types, not templating.

References:
- [ChecklistModel.ALLOWED_TYPES](src/shieldcraft/services/checklist/model.py)
- Failing tests referencing `pipeline`, `loader_stage`, and `engine_stage`.

