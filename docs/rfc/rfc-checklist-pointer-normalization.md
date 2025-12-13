# RFC: Checklist Pointer Normalization & Extraction

Problem statement (linked tests):
- Failing tests: [tests/test_checklist_generator.py](tests/test_checklist_generator.py), [tests/test_checklist_generator_expanded.py](tests/test_checklist_generator_expanded.py), [tests/test_checklist.py](tests/test_checklist.py)
- Summary: Checklist generation varies in which pointers are emitted (scalar nodes may be omitted; arrays with id-based segments differ). Tests expect items for simple scalar keys like `/x` to be present in the generated checklist. AST extraction and checklist normalization need clearer rules.

Current observed behavior:
- AST builder currently generates `dict_entry`, `array_item`, and `scalar` nodes; the checklist extractor only extracts certain node types, leaving out scalar fields in some cases and generating derived tasks with types not in allowed lists.

Proposed canonical rule:
- Checklist extraction should include nodes for: all dict entries (object entries), object elements (array items with dict values), and scalar leaf nodes (scalar values). The canonical pointer used for each checklist item should align with pointer_map semantics (id-based for arrays if IDs present).
- The normalized checklist item must include: `id`, `ptr`, `text`, `type`, `category`, `source_pointer`, `source_section`, and `requires_code` (boolean) to remove ambiguity for codegen routing.

Explicit invariants:
- Invariant: Scalar leaf nodes in the AST must be extracted as checklist items with `ptr` pointing to the leaf path and `type: task` unless a semantic `type` is specified on the parent object.
- Invariant: For array items, prefer `id` segments when present. If the element is an object and has a `type` or `template` field, the extracted checklist item should incorporate that `type` and `template` value.

Backward-compatibility notes:
- Existing scripts relying on old pointer paths must inspect pointer_map to find the canonical pointer or use `raw_ptr` fallback; engine should provide compatibility mapping for a limited transition window.

Out-of-scope items:
- UI or CLI consumer semantics for checklist items (this RFC focuses on generation shape only).

References:
- [ASTBuilder](src/shieldcraft/services/ast/builder.py)
- [SpecExtractor](src/shieldcraft/services/checklist/extractor.py)
- Tests: `tests/test_checklist_generator.py`, `tests/test_checklist_generator_expanded.py`

