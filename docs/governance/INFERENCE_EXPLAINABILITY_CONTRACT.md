# INFERENCE EXPLAINABILITY CONTRACT (AUTHORITATIVE)

This document defines the authoritative explainability metadata required for any synthesized,
coerced, inferred, or derived data emitted by the compiler and checklist pipeline.

Mandatory metadata fields (attached to checklist items or synthesized objects):
- `meta.source` — one of: `explicit | default | derived | coerced | inferred`
- `meta.justification` — short machine-readable string explaining why the value was created (e.g., `safe_default`, `missing_spec_pointer`, `heuristic_prose_keyword_match`). For BLOCKER/REFUSAL-related inferences the justification MUST reference affected pointer(s) via `meta.justification_ptr` or by embedding the pointer in the justification code.
- `meta.inference_type` — one of: `none | safe_default | heuristic | structural | fallback`
- `meta.tier` — when applicable: `A | B | C` (reflects the template tier per `TEMPLATE_COMPILATION_CONTRACT.md`)

Principles
- Any inference must be recorded in machine-readable fields above; missing explainability
  metadata is a compiler violation.
- Violations are classified by tier: Tier A missing explainability → BLOCKER; Tier B → DIAGNOSTIC; Tier C → advisory.
- Explainability metadata must be deterministic and include a short justification code suitable for audit and filtering.

Examples
- Synthesized default for missing `agents` (Tier A):
  - `meta.source = "default"`
  - `meta.justification = "safe_default_agents_list"`
  - `meta.inference_type = "safe_default"`
  - `meta.tier = "A"`

- Prose-derived confidence heuristic:
  - `meta.source = "inferred"`
  - `meta.justification = "heuristic_prose_keyword_match"`
  - `meta.inference_type = "heuristic"`
  - `meta.tier = "C"` (if informal)

Enforcement
- The compiler attaches explainability metadata at each inference site; unit tests and CI guards assert the presence.
- Tier A inferences without a corresponding checklist item or without explainability metadata are considered violations and will be detected via compiler assertions and failing tests.

Signed: Governance
Date: 2025-12-16
