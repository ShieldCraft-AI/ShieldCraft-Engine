# CHECKLIST SEMANTICS (AUTHORITATIVE)

Status: AUTHORITATIVE

Purpose
- Provide a concise, authoritative description of checklist semantics for the ShieldCraft engine and governance surface.
- This document records the contract that implementations are expected to honor (facts and contract only). It does not prescribe code changes or implementation details.

Checklist Item Classes
- ACTION
  - A checklist item representing a concrete implementable change or task that, when completed, advances the product toward satisfying a requirement.
  - Typical fields: `id`, `ptr`, `text`, `action`.

- BLOCKER
  - A checklist item that indicates a condition that must be resolved before safe progress can be made. Blockers are actionable but may be prioritized differently and can be blocking for automated execution.
  - Typical fields: `id`, `ptr`, `text`, `blocking: true`.

- REFUSAL
  - A checklist-level outcome that indicates the system deterministically refused to produce an executable artifact because required conditions (evidence, invariants, artifact producers, or safety checks) were not met.
  - A well-formed refusal is an explicit, successful outcome and MUST be emitted in place of an executable artifact.
  - Typical fields: `refusal: true`, `refusal_reason` (string), and contextual guidance in `items` or manifest.

- DIAGNOSTIC
  - A checklist item or artifact that assists authors with context, guidance, or debugging information (e.g., sufficiency reports, readiness traces, suppressed-signal reports). Diagnostics are advisory and do not by themselves indicate readiness.

Mandatory Checklist-level Fields (emitted by the engine)
- `emitted` (boolean or timestamp): indicates whether a final checklist artifact (or refusal) has been produced. The presence of `emitted` = true signals an explicit engine decision was persisted.
- `confidence` (string: e.g., "low" | "medium" | "high"): an explicit top-level or per-item indication of confidence in the checklist content.
- `refusal` (boolean): when true, indicates that the run concluded with a refusal outcome (an explicit, successful refusal).
- `refusal_reason` (string | null): human-readable reason for any refusal outcome; should reference which invariant, gate, or missing artifact caused the refusal.
- `safe_first_action` (object | null): when available, an advisory first safe action (or refusal_action) for authors/operators to take next; may be `null` when not applicable.

Emission Guarantee (Contract)
- Checklist emission is mandatory under all conditions.
  - For successful runs, a persisted `checklist.json` under self-host outputs (and an entry in the run manifest) must be produced.
  - For validation or contraction failures, a deterministic advisory artifact (e.g., `checklist_draft.json`) and/or an explicit `refusal` outcome and corresponding manifest entries must be produced.
- Under no circumstances may a run suppress emission by terminating with an uncaught exception, an early return that omits emitting artifacts, or by relying on validation failures to hide the absence of emission. Emission can be a draft, a refusal, or a final checklist; what matters is an explicit persisted artifact representing the engine decision.

Why Refusal Is a Successful Outcome
- A refusal indicates the engine made a deterministic, auditable decision to not produce an executable artifact due to missing evidence, invariant violations, safety constraints, or missing artifact producers.
- Refusal artifacts are actionable: they must contain `refusal_reason` and sufficient guidance or diagnostics so authors or operators can remediate and re-run.
- Treating refusal as a first-class success mode enables deterministic CI, reproducible auditing, and clearer governance traces.

What Went Wrong Previously (No‑Machine Failure Mode) — Facts Only
- Observed symptom: callers (trials runner) asserted "Checklist not emitted" even though a `checklist.json` artifact existed in the self-host output directory for the same run.
- Observed causes (factual):
  - Some control paths in the orchestration code relied on subsequent checks or side-effects and could overwrite detection flags or re-evaluate emission state after a previously-observed emission was detected (e.g., clearing an emission flag when `spec_feedback.json` was missing).
  - Validation-failure paths sometimes wrote only advisory preview artifacts (e.g., `checklist_draft.json`) and then applied a primary-artifact invariant that raised when both `checklist_draft.json` and `refusal_report.json` were present, producing an error instead of persisting a single canonical artifact.
  - Post-generation post-processing (minimality/inference/execution-plan checks) can raise fatal errors that prevent the final persistence step even when generator returned an in-memory checklist result.
- Net effect: the absence of a single, deterministic persisted artifact representing the engine outcome caused client-side brittle checks and false-negative detection of "no checklist emitted."

Owner and Authority
- Owner: Governance (docs/governance)
- This document is AUTHORITATIVE: it records the contract that implementations must respect. Implementation-level remediation is tracked separately (decision-log / issue tracker).

Change History
- 2025-12-16: Document created and marked AUTHORITATIVE.
