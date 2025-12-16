# CHECKLIST EMISSION CONTRACT (AUTHORITATIVE)

Status: AUTHORITATIVE

Single Invariant
- Checklist emission is mandatory for every engine run. A persisted artifact must capture the engine's outcome for every run; acceptable artifacts include a final `checklist.json`, a well-formed `refusal` artifact, or an explicit persisted draft (`checklist_draft.json`) accompanied by a manifest entry that records the run outcome.

Policy — Forbidden Patterns
- Under no circumstances shall a run suppress emitted results via:
  - uncaught exceptions that abort run without emitting an artifact,
  - early `return` paths that omit persisting an outcome artifact,
  - validation/sync/quality/persona/schema/test failures that cause silent termination without producing a persisted checklist or refusal artifact.
- Runs must persist an outcome artifact even when the run concludes with a refusal, validation advisory, or diagnostic-only result.

Allowed Checklist Outcomes (canonical)
- ACTION — implementable task(s) to advance the spec toward an invariant.
- BLOCKER — a condition that blocks safe progress and requires remediation.
- REFUSAL — an explicit, auditable refusal to emit executable artifacts because required conditions were unmet (must include `refusal_reason`).
- DIAGNOSTIC — advisory artifacts or reports (sufficiency, readiness trace, suppressed-signal report) that augment the persisted outcome.

Representation Requirements (high-level)
- Every outcome artifact must include metadata enabling auditability: `emitted` indicator, `refusal` boolean when applicable, `refusal_reason` text when refusal is true, `confidence` level, and a manifest entry linking the run fingerprint and outputs.
- Failures in validation, sync, persona vetoes, schema checks, quality gates, or test-attached enforcement MUST be represented as checklist items or an explicit refusal artifact, not as a silent hard-fail that leaves no persisted outcome.

Scope and Authority
- Owner: Governance (docs/governance)
- Authority: This document is AUTHORITATIVE and governs expected engine behavior at a policy level. Implementation details and remediations are tracked separately and require implementation PRs referencing this contract.

Change History
- 2025-12-16: Document created and marked AUTHORITATIVE.

Reporting Discipline (Copilot)
- Scope: Applies to all Copilot-generated governance reports and policy summaries produced in this repository; this rule is authoritative for Copilot reporting in `docs/governance`.
- Default report format (required): concise, structured bullets only: 1) Summary — 1–2 sentences; 2) Actions Taken — bulleted list of edits; 3) Files Modified — bulleted list; 4) Next Steps — single-line recommendation.
- Forbidden reporting behaviors: no long-form narrative; no speculative analysis; no disclosure of internal system or developer instructions; no step-by-step tool/process logs; no persona or model identity claims beyond the fixed preamble rules.
- Contract enforcement: Excessive verbosity that dilutes actionable signals is a contract violation; Governance reviewers may require edits or record violations in the decision log.
- Authority & scope: Governance (docs/governance). This policy is documentation-only; no runtime, schema, or engine changes were made.
- Effective: 2025-12-16
