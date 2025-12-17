# Compilation Phase Model

The compiler is structured as a fixed sequence of deterministic phases. Each phase has well-defined inputs, outputs, and allowed failure modes.

Fixed phases
1. Ingestion
   - Inputs: canonical spec (and optional AST)
   - Outputs: raw AST traversal items
   - Allowed failures: schema failures recorded as DIAGNOSTIC events
2. Normalization
   - Inputs: raw items
   - Outputs: enriched items (classification, severity, metadata)
   - Allowed failures: missing lineage recorded as DIAGNOSTIC
3. Constraint propagation
   - Inputs: normalized items and spec constraints
   - Outputs: additional constraint items, merged constraints
   - Allowed failures: constraint violations recorded as BLOCKER
4. Synthesis
   - Inputs: merged items, derived tasks, invariants results
   - Outputs: final_items (stable ids, order ranks)
   - Allowed failures: generation contract failures (BLOCKER)
5. Finalization
   - Inputs: final_items
   - Outputs: serializable result object (`valid`, `items`, `preflight`, `lineage`, `diff`, etc.)
   - Allowed failures: test gate failure results returned as partial results

Mapping gates (G1–G22) to phases
- Ingestion: G4_SCHEMA_VALIDATION
- Normalization: G9_GENERATOR_RUN_FUZZ_GATE, G10_GENERATOR_PREP_MISSING
- Constraint propagation: G8_TEST_ATTACHMENT_CONTRACT
- Synthesis: G13_GENERATION_CONTRACT_FAILED, G16_MINIMALITY_INVARIANT_FAILED
- Finalization: G20_QUALITY_GATE_FAILED, G22_EXECUTE_INTERNAL_ERROR_RETURN

Note: This model is prescriptive: gates are classified by where they must be recorded. The mapping is authoritative and must not be changed without governance approval.
