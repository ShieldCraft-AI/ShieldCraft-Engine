<!-- AUTHORITATIVE -->
# Template Compilation Contract (Phase 3.1)

**Owner:** Governance (docs/governance)

**Scope:** This document is **AUTHORITATIVE** for the interpretation of the product specification template (`spec/se_dsl_v1.template.json`) with respect to **checklist compilation** only. It is a policy contract (documentation-only). No runtime behavior, schema, persona, or engine code is changed by this document.

## Summary

- **Purpose:** Prevent suppression, drift, or misinterpretation of top-level template sections by establishing a strict tiering and an explicit absence policy for how the checklist compiler consumes template data.
- **Evidence base:** SE_GATE_AUDIT_V1, SE_GATE_AUDIT_V1_COMPLETENESS_CHECK, template_to_engine_mapping_report, CHECKLIST_EMISSION_CONTRACT.md, GATE_HANDLING_POLICY.md, decision_log.md entries recorded on 2025-12-16.

## Tiering Definitions

- **Tier A — Checklist-Critical:** Absence or incomplete values for these sections MUST result in emitted checklist items or safe defaults; absence MUST NEVER cause an exception, early return, refusal, or artifact suppression.
- **Tier B — Checklist-Influencing:** These sections may affect checklist priority, readiness gating, or blocking classification. Missing/incomplete values SHOULD produce checklist items or safe defaults; they MUST NOT cause silent suppression of checklist artifacts.
- **Tier C — Informational / Deferred:** Informational by intent. These sections MAY be ignored safely by the compiler when absent and MUST NOT cause checklist suppression; if a section has no runtime consumer it is Tier C and marked NOT CONSUMED.

## Tier Classification (every top-level section listed exactly once)

- **metadata — Tier A**
  - Rationale (facts-only): Consumed for `product_id`, `generator_version`, `enforce_tests_attached` flags and manifest writing (see `src/shieldcraft/engine.py`, `src/shieldcraft/dsl/loader.py`, `src/shieldcraft/services/checklist/constraints.py`). Missing metadata fields are already converted into checklist tasks by constraints; therefore metadata is Checklist-Critical.

- **determinism — Tier B**
  - Rationale (facts-only): Determinism snapshots are attached by the generator (`_determinism`) and checked by readiness logic (`src/shieldcraft/verification/readiness_evaluator.py`). Missing determinism results in a `determinism_replay` gate failure that influences readiness and blocking classification; therefore Tier B.

- **agents — Tier A**
  - Rationale (facts-only): `agents` fields are inspected by checklist semantic & constraint checks (missing `type` → emitted checklist task `/agents/{i}/type`) and these items are actionable. Operational agent runtimes are not implemented in this repository (semantic checks exist; no agent orchestrator found). The compiler MUST emit checklist items for missing agent metadata rather than suppressing output.

- **pipeline — Tier C (NOT CONSUMED)**
  - Rationale (facts-only): The template provides `pipeline.states` and `transitions` but a review found no implemented runtime state machine consumer in this repository; template presence is documented and exercised in tests/docs only. Mark as NOT CONSUMED.

- **artifact_contract — Tier B**
  - Rationale (facts-only): Used by artifact summary and coverage helpers (`src/shieldcraft/services/guidance/artifact_contract.py`, `src/shieldcraft/services/io/manifest_writer.py`) and influences artifact expectations and coverage summaries. Absence should produce checklist hints/tasks; it influences readiness/CI expectations.

- **error_contract — Tier C**
  - Rationale (facts-only): Present in the template and schema, but runtime usage is limited and primarily informative; canonicalizer and tooling record the schema but no centralized enforcement hook was found to justify a blocking classification.

- **evidence_bundle — Tier A**
  - Rationale (facts-only): Evidence is constructed and included in manifests and checklist outputs (`src/shieldcraft/services/governance/evidence.py`, `src/shieldcraft/services/checklist/evidence.py`). Evidence absence or insufficiency is material to checklist completeness and must be represented by checklist items/annotations; the compiler MUST ensure evidence problems are represented in checklist items and MUST NOT suppress a checklist artifact when evidence is missing or invalid.

- **ci_contract — Tier C**
  - Rationale (facts-only): Referenced by tests and docs and used by CI guidance; no central runtime enforcement was found in engine code. Treat as informational and classify as Tier C.

- **generation_mappings — Tier B**
  - Rationale (facts-only): Used by codegen/mapping inspector and influences whether checklist items map to codegen targets (`src/shieldcraft/services/codegen/mapping_inspector.py`, `src/shieldcraft/services/codegen/generator.py`). Missing mapping can cause items to be recorded as `no_mapping` (affects generation outcomes) so this section influences checklist→codegen mapping and belongs in Tier B.

- **observability — Tier C**
  - Rationale (facts-only): Emitted for audit and observability (`src/shieldcraft/observability/__init__.py`); engine wraps observability calls to avoid altering behavior. Observability signals are informative and must not be treated as blocking checklist input.

- **security — Tier B**
  - Rationale (facts-only): Self-host input allowances and `allowed_paths` are consulted by self-host guards and can lead to `disallowed_selfhost_input` / refusal behavior (`src/shieldcraft/services/selfhost/__init__.py`, `src/shieldcraft/engine.py:444-456`). These affect whether a run proceeds under self-host mode and therefore influence checklist emission readiness; classify as Tier B.

## Absence Policy (AUTHORITATIVE)

1. Missing data MUST result in emitted checklist items or stable defaults. The checklist compiler MUST transform absence into explicit checklist items or documented defaults rather than silently suppressing artifact emission.
2. Missing data MUST NOT cause a raise, early return, silent refusal, or non-emission of the checklist artifact. Any existing code paths that raise due to missing template data are governance misalignments to be remediated via implementation work (tracked separately).
3. Schema validation failures (syntactic or structural) MUST be represented inside the checklist as checklist items (for example, `schema_error` entries) and MUST NOT be used as the sole mechanism to prevent emitting a checklist artifact. If an emitting run also needs to report structured schema failures, these failures should appear as checklist entries (with clear reason codes) and corresponding `errors.json` / `refusal_report.json` as applicable, but the engine MUST persist an outcome artifact.

## Compiler Promise (exact authoritative text)

Given a syntactically valid spec, ShieldCraft MUST emit a checklist artifact. Validation failures are represented inside the checklist, not instead of it.

## Operational Notes & Rationale

- This document is policy-only and records the preferred, authoritative mapping and absence handling expectations for implementers and reviewers. Implementation changes to enforce the above expectations (converting suppressing gates to explicit checklist annotations/refusals) will be tracked as separate engineering tasks referencing this contract and the Gate Inventory (SE_GATE_AUDIT_V1).
- For any future template section additions, the author MUST update this contract and classify the section into Tier A/B/C with evidence references.

## References

- SE_GATE_AUDIT_V1
- SE_GATE_AUDIT_V1_COMPLETENESS_CHECK
- template_to_engine_mapping_report
- docs/governance/CHECKLIST_EMISSION_CONTRACT.md
- docs/governance/GATE_HANDLING_POLICY.md

Signed: Governance
Date: 2025-12-16
