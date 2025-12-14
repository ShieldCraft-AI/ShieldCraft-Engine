# Phase 14 — Self-Hosting Validation Closure Report

Date: 2025-12-13
Phase ID: Phase 14 (self-hosting-validation)
Outcome: Failure (non-passing)

## Phase Objective
- Validate self-hosted pipeline determinism and artifact generation for the canonical DSL sample specs.
- Produce deterministic `manifest.json`, `summary.json`, and `generated/` outputs for the self-host run.

## Execution Summary
- Ran self-host pipeline using a canonical sample spec twice; artifacts saved to `artifacts/self_hosting_run_1` and `artifacts/self_hosting_run_2`.
- Determinism verification (manifest + summary + generated outputs) succeeded for the runs executed in the self-host pipeline.
- Executed a full test suite locally: 224 passing, 55 failing (triaged into categories in `docs/self_hosting_failure_triage.md`).
- All failures were classified; no fixes or functional changes were applied during this validation phase.

## Determinism Status
- Determinism Status: FAIL (overall validation cannot pass due to failing tests and blocking defects).
- Note: The deterministic nature of the pipeline artifacts was confirmed where the self-host runs completed successfully; however the presence of 55 failing tests blocks closure as 'pass'.

## Blocking Defect Categories (Summary)
- Generator lockfile / preflight contract enforcement (raises exceptions instead of returning violations).
- DSL version enforcement mismatch (`metadata.spec_format` vs `dsl_version` expectations).
- Evidence bundle API incompatibility (`invariants` and `graph` required by new signatures).
- CodeGenerator output shape mismatches (variable list/dict shapes cause downstream failures).
- Pointer map canonicalization vs index-based pointer usage (AST vs pointer_map mismatches).
- Pointer coverage report shape inconsistencies.
- Checklist ID canonicalization differences (stable ID expected vs legacy `TASK-####`).
- JSON canonical formatting (unicode escaping vs direct characters causing deterministic formatting differences).
- Cross-section return type mismatches (functions returning wrong types in code paths).
- Self-host manifest summary generation missing on validation failures.

For full details, see: `docs/self_hosting_failure_triage.md`.

## Explicit Closure Statement
- Phase 14 is CLOSED with a non-passing outcome (`FAIL`).
- The self-hosting pipeline achieved deterministic artifact generation in the narrow self-host run, but the engine, codegen, and checklist contracts are not fully compatible with the spec schema changes performed during Phase 13.
- No code fixes were applied during this phase; only triage and validation were performed per the Phase 14 contract.

## Required Inputs for Remediation Phase
To proceed with remediation and for re-attempting Phase 14 validation, the following inputs and actions are required:
- Per-RFC PRs to address each triaged category, including tests and schema updates where needed.
- A prioritization ticket for the top blocking defects: generator contract, DSL mapping, evidence bundle compatibility, codegen shape standardization.
- A CI gating plan ensuring PR-level tests include the deterministic self-host run and `pytest -q` pass conditions.
- Migration guidance for legacy specs and a `SHIELDCRAFT_LENIENT_TYPES` migration guard where appropriate.
- A checklist of acceptance criteria and a re-test plan for Phase 14: self-host determinism + full test suite pass.

## Handoff
- This closure report, the triage file (`docs/self_hosting_failure_triage.md`), and the artifacts in `artifacts/self_hosting_run_1` and `_run_2` are the canonical handoff for the remediation phase.
- For each triaged category, create targeted PRs that follow the RFC per-PR structure and run CI with the full test suite and self-host validation before marking as resolved.

---

Status: CLOSED (FAIL)

