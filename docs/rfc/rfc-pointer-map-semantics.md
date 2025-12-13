# RFC: Spec Pointer Map Semantics (IDs vs Indexes)

Problem statement (linked tests):
- Failing tests: [tests/spec/test_pointer_map.py](tests/spec/test_pointer_map.py), [tests/spec/test_pointer_missing.py](tests/spec/test_pointer_missing.py), [tests/selfhost/test_governance_and_pointers.py](tests/selfhost/test_governance_and_pointers.py)
- Summary: Pointer map/coverage tests and pointer auditor expect consistent mapping of AST pointers to raw spec pointers. Changes to pointer canonicalization (preferring `id` for list segments when present) affected pointer map resolution and uncovered pointers.

Current observed behavior:
- AST builder uses `id` values for list pointer segments when all items have `id`; older pointer_map.json uses numeric indices (e.g., `/sections/0` vs `/sections/bootstrap`). This produces mismatches in pointer_map and coverage reports.
- `ensure_full_pointer_coverage()` currently produces a coverage structure; tests and manifests expect a specific shape (e.g., `total_pointers`, `ok_count`, and `missing_count`) while we currently return a different shape.

Proposed canonical rule:
- Canonical pointer mapping: For arrays of objects where all elements include an `id` field, use the `id` string as the JSON pointer segment for human-readability and stability (e.g., `/sections/bootstrap/items/item1`), and make pointer_map.json align with id-based pointers by default.
- Pointer map should provide both `raw_ptr` (numeric index) and `canonical_ptr` (id-based) entries for compatibility and transition.
- Coverage audit output should adhere to the standard manifest schema (`total_pointers`, `ok_count`, `missing_count`, `missing_ptrs`, `ok`: list, `missing`: list).

Explicit invariants:
- Invariant: The AST pointer -> pointer_map mapping must provide canonical id-based paths when IDs are present; the `pointer_map.json` must include both `raw` and `canonical` pointers for each entry for backward compatibility.
- Invariant: Coverage audit must always include `total_pointers`, `ok_count`, `missing_count`, `ok`, and `missing` keys in returned coverage objects to meet preflight expectations.

Backward-compatibility notes:
- Existing pointer_map consumer scripts may rely on numeric indices: scripts must consult `raw_ptr` when IDs are absent; if present, they must prefer `canonical_ptr`.
- Migration: Add a transition window and a linter tool that maps old numeric pointers to canonical id pointers for test/data migrations.

Out-of-scope items:
- Changes to user-facing UIs; this RFC focuses on canonical pointer semantics and backward compatibility outputs.

References:
- [test_pointer_map.py](tests/spec/test_pointer_map.py)
- [test_pointer_missing.py](tests/spec/test_pointer_missing.py)

