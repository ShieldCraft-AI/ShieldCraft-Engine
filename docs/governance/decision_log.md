# RFC Decision Log

Authoritative decisions made on 2025-12-13 (Phase 13 kickoff). All decisions recorded are spec-only; implementation requires separate PRs referencing RFC approvals.

## rfc-generator-version-contract.md
- Decision: APPROVE
- Rationale: A strict generator lockfile and `metadata.generator_version` requirement enforce reproducibility and CI safety. Explicit `generator_version` reduces surprises in preflight and ensures traceability.
- Effective scope: Spec-only; requires linter/migration guidance and CLI flags for a migration window.
- Blocking dependencies: `generators/lockfile.json` management and CI upgrade; adoption plan must include a migration tool.

## rfc-allowed-checklist-types.md
- Decision: APPROVE (with migration guard)
- Rationale: A canonical `type` enum prevents ad-hoc types and supports deterministic codegen and classification.
- Effective scope: Spec-only (schema change); migration scripts and `--lenient-types` flag should be implemented in a follow-up PR.
- Blocking dependencies: Adoption plan for migration, PRs to update schema and linter rules.

## rfc-pointer-map-semantics.md
- Decision: APPROVE
- Rationale: Canonical id-based pointers for arrays improve readability and determinism; providing `raw_ptr` ensures backward compatibility for consumers of numeric indices.
- Effective scope: Spec-only; requires pointer_map migration and test fixture updates.
- Blocking dependencies: Migration scripts to map numeric pointers to canonical pointers, and update pointer_map consumers.

## rfc-checklist-pointer-normalization.md
- Decision: APPROVE
- Rationale: Checklist extraction should include scalar leaf nodes and `requires_code` to enable correct codegen routing and ensure no items are inadvertently omitted.
- Effective scope: Spec-only; affects checklist schema and generator preflight validation.
- Blocking dependencies: Pointer map semantics RFC and allowed types RFC (to determine classification rules).

## rfc-bootstrap-artifacts.md
- Decision: APPROVE
- Rationale: Clear bootstrap artifact emission semantics reduce ambiguity and ensure self-host runs produce predictable bootstrap outputs and `summary.json` for CI/instrumentation.
- Effective scope: Spec-only; impacts self-host run contract and generator preflight.
- Blocking dependencies: Allowed checklist types RFC (defines bootstrap types), pointer normalization RFC (ensures pointer mapping for bootstrap tasks).

## Audit: Check for unambiguous decision status
- All RFCs above are provided with explicit decisions and rationale. There are no implicit approvals.
- Deferred RFCs: None.

## TAC_OPT_IN_V1
- Decision: LOCKED
- Rationale:
	- Early specs must be allowed to run without full test binding.
	- TAC is a quality accelerator, not a bootstrap blocker.
	- Spec-driven enforcement remains available when explicitly enabled.
- Mechanism:
	- Environment flag: `SHIELDCRAFT_ENFORCE_TEST_ATTACHMENT=1`
	- Spec flag: `metadata.enforce_tests_attached=true`
- Effective scope: Implementation-level (engine preflight enforcement)
- Status: LOCKED


## Checklist Semantics Contract Introduced (2025-12-16)
- Decision: RECORD (contract document created)
- Summary: An authoritative checklist semantics contract (`docs/governance/CHECKLIST_SEMANTICS.md`) has been added and marks emission as a mandatory, auditable outcome for engine runs (final checklist or explicit refusal).
- Observations (facts-only): multiple engine gates were found that, in current behavior, can prevent a persisted checklist artifact from being emitted (e.g., validation short-circuits, post-processing exceptions, and primary-artifact invariants in `main.run_self_host`).
- Action (policy statement only): remediation will convert such gates into checklist annotations or refusal outcomes so that an explicit persisted artifact represents each run's outcome (no implementation details recorded here).
- Notes: This entry records the contract and the observed misalignment with current engine behavior; implementation work will be tracked separately.


## Persona Protocol Review Deferred (2025-12-16)
- Decision: DEFER
- Rationale (facts-only): Persona behaviour and enforcement intersect with checklist semantics; evaluating persona protocols before the checklist emission contract is implemented risks inconsistent behavior and unauthorized vetoes.
- Policy: Persona protocol review and any persona-driven behavioral changes are explicitly postponed until the Checklist Semantics Contract is implemented and verified.
- Constraint: No changes to persona behavior, enforcement, or veto handling are authorized before the checklist emission contract milestone is achieved and documented.


## Checklist Emission Normalization – Phase 1 (2025-12-16)
- Decision: RECORD
- Summary (facts-only): The governance contract `CHECKLIST_EMISSION_CONTRACT.md` and gate handling policy `GATE_HANDLING_POLICY.md` have been created to assert that every engine run must persist an outcome artifact (final checklist or explicit refusal). Current engine behavior was observed to permit control-flow-driven suppression of emitted outcomes (see Gate Inventory G1–G22 and completeness findings G20–G22).
- Policy statement: Remediation work will convert gates that presently result in suppressed emission into checklist annotations or explicit refusals; this entry records intent and alignment with governance only (no implementation details or fixes are proposed here).
- Constraints: No persona behavior changes or runtime code changes are authorized as part of this recorded decision.

## Phase 4 Complete — Checklist Emission Normalization (2025-12-16)
- Decision: RECORD
- Summary (facts-only): Implementation work for Phase 4 (Checklist Emission Normalization) is complete. The engine now guarantees a persisted checklist artifact for every run via centralized finalization (the `finalize_checklist(...)` boundary). Schema validation failures, disallowed self-host artifacts, and `run_self_build` propagation behaviors that previously could suppress emission have been normalized so that outcomes are recorded and a checklist artifact is returned or persisted.
- Resolved MUST_NORMALIZE items (facts-only):
	- `G4` (schema validation) — schema failures are recorded as DIAGNOSTIC events and returned via `finalize_checklist`.
	- `G15` (disallowed self-host artifact) — disallowed artifact detection now records a REFUSAL event before the existing raise to ensure the refusal is captured in the checklist.
	- `run_self_build` propagation — `run_self_build` now propagates a finalized checklist returned by `run_self_host` instead of raising `selfhost_failed` when `run_self_host` already produced a finalized outcome.
- Preserved behavior (facts-only): All ALLOWED_HARD_FAIL gates (REFUSAL raises, persona veto semantics, and other authorized hard failures) were preserved unchanged; REFUSALs continue to raise locally but are recorded so the centralized boundary emits a checklist artifact.
- Constraints verified (facts-only): Persona protocol, schema design, and template structure were not modified as part of this work; no new gate IDs were introduced in Phase 4.
- Tone: factual and declarative — this entry records completion and the narrow, authoritative changes made to satisfy the Checklist Emission Invariant.


## Template Compilation Contract Locked (Phase 3.1) (2025-12-16)
- Decision: LOCKED
- Rationale (facts-only): Template over-expression and unclear consumption historically contributed to checklist emission drift (sections un-matched to consumers, absent fields causing raises or non-emission). To address this, a tiering model and a strict absence policy have been introduced to govern interpretation.
- Summary: The authoritative contract `docs/governance/TEMPLATE_COMPILATION_CONTRACT.md` is now locked for template→checklist compilation interpretation. It classifies every top-level template section into Tier A/B/C and mandates absence handling that prevents suppression of persisted checklist artifacts.
- Effective scope: Documentation-only policy (spec->checklist compilation). No runtime behavior, schema, or persona changes were made in this phase.
- Action: Implementation-level remediation (converting suppression gates to explicit checklist annotations/refusals) will be tracked in follow-up engineering tasks referencing SE_GATE_AUDIT_V1 and this contract.

## Copilot Reporting Discipline Enforced (2025-12-16)
- Decision: LOCKED
- Rationale (facts-only): Excessive verbosity in Copilot-generated reports caused signal dilution in governance review workflows and risked misinterpretation of findings.
- Summary: Governance mandates a concise, structured Copilot reporting format (see `docs/governance/CHECKLIST_EMISSION_CONTRACT.md` — "Reporting Discipline (Copilot)"). Excessive verbosity is a contract violation for Copilot-generated outputs.
- Effective scope: Documentation-only policy. No runtime, schema, persona, or engine changes were made as part of this decision.
- Owner: Governance (docs/governance)


## Phase 4 Closed — Checklist Emission Invariant Locked
- Decision: RECORD
- Summary (facts-only): Phase 4 (Checklist Emission Normalization) is closed and the Checklist Emission Invariant has been locked: all known suppression paths have been normalized or guarded and the centralized emission boundary `finalize_checklist(...)` is the single authoritative emitter of finalized checklist artifacts.
- Explicit state:
	- Phase 4 is complete and implemented in code and tests.
	- Known suppression paths have been normalized (converted into recorded gate events and finalized results) or guarded by assertions.
	- Remaining raises in the codebase are intentional REFUSAL hard-fails and are recorded as gate events before being raised.
	- No persona, schema, or template semantics were altered as part of this closure.
	- Future work on persona protocol or semantics is deferred and out of scope for this decision.
- Rationale: Provide an auditable stop condition and an authoritative code-level guard to prevent emission regressions.


## Phase 5 Closed — Semantic Meaning Locked
- Decision: RECORD
- Summary (facts-only): Phase 5 (Semantic Lock) is complete. Checklist semantics are locked: a single canonical `primary_outcome` is derived for every run, every checklist item is assigned a single deterministic `role`, and semantic invariants are enforced by code-level assertions and deterministic tests.
- Explicit state:
  - Primary outcome precedence (REFUSAL > BLOCKED > DIAGNOSTIC_ONLY > SUCCESS) is implemented and tested.
  - Deterministic `PRIMARY_CAUSE` selection with lexicographic gate tie-break and earliest occurrence as a final tie-break is implemented and tested.
  - Semantic stability assertion added to ensure deterministic, byte-stable output for identical inputs.
  - No persona, schema, or gate-ID changes were made; all logic was centralized in `finalize_checklist`.
- Rationale: Lock semantic meanings to prevent regressions and ensure deterministic artifact semantics; changes to semantics require governance approval and a new implementation phase.


## Phase 6 Closed — Persona Arbitration Simplified
- Decision: RECORD
- Summary (facts-only): Phase 6 (Persona Arbitration Simplification) is complete. Persona authority, routing, and event compression were introduced as defensive, deterministic, metadata-only changes and documentation. Persona outputs remain auditable evidence and do not, by themselves, alter canonical checklist semantics.
- Explicit state:
  - A Persona Authority Model (DECISIVE|ADVISORY|ANNOTATIVE) was introduced as metadata; persona dataclasses now carry an optional `authority` attribute.
  - Deterministic, static persona routing (configurable) is available via `src/shieldcraft/persona/routing.py`; discovery falls back to `scope` when routing is not configured.
  - Persona events are compressed into a deterministic `checklist.persona_summary` structure for auditability; primary persona cause is selected deterministically and traceably.
  - Legacy persona protocol artifacts were marked for deprecation and archived as informational references.
- Rationale: Simplify persona arbitration while preserving auditability, determinism, and decision authority; future runtime enforcement of authority classes will be gated by governance decisions.


## Phase 7 Closed — Persona Protocol Consolidated
- Decision: RECORD
- Summary (facts-only): Phase 7 (Persona Protocol Consolidation) is complete. The persona protocol has been consolidated into a minimal, authoritative core (`docs/persona/PERSONA_PROTOCOL.md`), supporting documents were rewritten as references or archived, and deprecation markers were added for legacy mechanisms.
- Explicit state:
  - The canonical `PERSONA_PROTOCOL.md` is the single authoritative protocol for persona behavior, authority classes, routing, decision precedence, and event emission rules.
  - Supporting operational documents reference the canonical core and legacy materials are archived as historical references (`docs/persona/legacy/`).
  - A documented inventory, gaps report, and simplification summary accompany the consolidation (`docs/governance/PERSONA_DOCUMENT_INVENTORY.md`, `PERSONA_PROTOCOL_GAPS.md`, `PERSONA_PROTOCOL_SIMPLIFICATION_SUMMARY.md`).
- Rationale: Reduce documentation surface, make persona expectations explicit and auditable, and preserve historical artifacts for traceability; no runtime behavior was changed in Phase 7.
