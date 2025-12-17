# Compiler Failure Normalization (AUTHORITATIVE MATRIX)

This document defines the failure normalization matrix: mapping of Gate → Phase → Event Type → Checklist Item Type.

Matrix (representative examples)
- G4_SCHEMA_VALIDATION → Ingestion → DIAGNOSTIC → DIAGNOSTIC
- G9_GENERATOR_RUN_FUZZ_GATE → Normalization → BLOCKER → BLOCKER
- G10_GENERATOR_PREP_MISSING → Normalization → DIAGNOSTIC → DIAGNOSTIC
- G11_RUN_TEST_GATE → Synthesis → BLOCKER → BLOCKER
- G13_GENERATION_CONTRACT_FAILED → Synthesis → BLOCKER → BLOCKER
- G16_MINIMALITY_INVARIANT_FAILED → Synthesis → REFUSAL → REFUSAL
- G20_QUALITY_GATE_FAILED → Finalization → REFUSAL → REFUSAL
- G22_EXECUTE_INTERNAL_ERROR_RETURN → Finalization → DIAGNOSTIC → DIAGNOSTIC

Constraints
- No new gate IDs may be introduced by this phase.
- This mapping must be aligned with `finalize_checklist` behavior and the Semantic Outcome Invariants.

Behavioral note
- A gate may record an event with outcome REFUSAL or BLOCKER; the compiler must ensure such events are surfaced in the final checklist as checklist items and influence primary outcome derivation via `finalize_checklist`.
