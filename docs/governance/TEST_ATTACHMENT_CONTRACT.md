# Test Attachment Contract (TAC) v1

This document is the single-source authoritative contract for Test Attachment
in ShieldCraft verification (TAC v1). It defines the minimal, non-negotiable
requirements that must be satisfied for a checklist item to be considered
covered by tests.

Contract rules (exact semantics):

- `test_refs` MUST be present on every checklist item.
- `test_refs` MUST be an array of strings.
- `test_refs` MUST have length >= 1 (non-empty array).
- Each entry in `test_refs` MUST be a string identifier referencing a discovered
  test in the test registry.

Failure behavior:

- Violation of TAC MUST be classified as `PRODUCT_INVARIANT_FAILURE`.
- The verification gate `tests_attached` MUST fail deterministically with error
  code `tests_attached` and include the list of offending checklist item ids.
- TAC enforcement is mandatory before any instruction emission (pre-execution
  block). Do not proceed on TAC failure.

Notes:

- This contract enforces traceability from checklist items to executable tests;
  it does not prescribe test content or adequacy — only that a concrete test
  reference exists and is syntactically valid.
