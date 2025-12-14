# SE Readiness Signal

This document defines the SE Readiness signal emitted by the Engine. The readiness
signal is a verification-only artifact and does not change runtime behavior. It
indicates whether the spec + checklist have passed a set of deterministic
verification gates.

Gates included:

- `spec_fuzz_stability`: deterministic spec fuzzing detects contradictions or drift.
- `tests_attached`: every checklist item must have explicit, traceable tests attached.
- `persona_no_veto`: no active persona vetoes may be present.
- `determinism_replay`: recorded seeds + snapshot must replay identically.

Readiness is explicit: the Engine attaches `_readiness` (structured verdict) and
`_readiness_report` (human-readable text) to generated checklist outputs. The
readiness report always contains either a clear `OK` or `NOT READY` state and
reasons for any failures.

This signal is used for operational gating (CI, self-host runs) and for audit.
