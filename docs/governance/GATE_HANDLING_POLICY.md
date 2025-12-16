# GATE HANDLING POLICY

Status: Governance policy (implementation-agnostic)

Gate Classes
- Preflight gates: sync, schema, instruction validation, governance presence, and early persona veto checks.
- Generation gates: checklist generator internal validations, invariant checks, semantic gates, and test gates.
- Post-generation gates: artifact emission locks, minimality/equivalence, execution-plan verification, quality gates, and filesystem/IO failures.

Required Behavior
- Preflight gates: when a preflight gate triggers a failure that prevents normal generation, the engine MUST emit a persisted artifact recording the failure as one or more checklist items or an explicit refusal artifact (include `refusal_reason` and diagnostics).
- Generation gates: internal generator validation errors that prevent normal item synthesis MUST be reflected in the returned checklist result; the engine MUST persist the resulting checklist (possibly with `valid: false` and `reason` fields) or emit an explicit refusal artifact.
- Post-generation gates: gates that inspect emitted artifacts (quality, minimality, execution plan) MUST either:
  - annotate the checklist and persist it (if the run outcome is advisory or remediable), or
  - emit an explicit refusal artifact with `refusal_reason` if the artifact cannot be safely produced.

Allowed Hard-Fail Categories
- Only the following are allowed to propagate as immediate hard-fail runtime errors (i.e., no checklist persistence possible):
  1. Catastrophic runtime corruption (process memory corruption, interpreter crash).
  2. Filesystem write failures that prevent any artifact persistence (disk full, permission error) as determined by a persisted IO error state.
  3. Security-critical breaches that require immediate abort and out-of-band incident handling.
- All other gate outcomes must be represented via checklist annotations or an explicit refusal artifact (policy requirement).

Gate IDs and References
- Applicable gate IDs: G1–G22 (see Gate Inventory in `tmp.txt` for details). Implementations should consult the Gate Inventory when classifying real failures.

Policy Notes
- This policy is intentionally implementation-agnostic and does not prescribe code changes or refactors. It defines required behaviors for gate handling to ensure every run has an auditable persisted outcome.

Change History
- 2025-12-16: Policy created and published in governance docs.
