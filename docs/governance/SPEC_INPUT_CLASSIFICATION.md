# Spec Input Classification (COMPILER INPUT TIERING)

This document enumerates spec sections and their classification with respect to the Spec→Checklist compiler. Classifications are REQUIRED, OPTIONAL, IGNORED, or FUTURE.

Classification rules (aligns to Phase 3 tiering)
- REQUIRED: Sections the compiler expects to be present to produce deterministic items. Missing REQUIRED data must be recorded as a diagnostic or refusal event; absence must not cause silent non-emission.
- OPTIONAL: Sections that influence enrichment (e.g., `metadata`) but whose absence is tolerated and results in default behaviors.
- IGNORED: Sections that are used by other subsystems (e.g., deployment) and explicitly ignored by the compiler.
- FUTURE: Reserved areas for future extensions; presence must not change core compilation semantics unless a governance-approved reopening occurs.

Canonical classification (non-exhaustive)
- `metadata` → OPTIONAL
- `instructions` → REQUIRED (if present, must validate and bind tasks)
- `rules_contract` → OPTIONAL
- `invariants` → OPTIONAL (compiler will evaluate and translate to checklist items)
- `templates` / `template_sections` → REQUIRED/OPTIONAL depending on product tier (see Phase 3 Template Contract)
- `tests` → OPTIONAL (used by test attachment contract)

Default behavior on missing REQUIRED data
- The compiler must record a DIAGNOSTIC or REFUSAL gate event and return a partial/invalid result; it must not raise in a way that prevents the caller (engine) from calling `finalize_checklist(...)`.

Constraints
- This classification aligns with Phase 3 tiering and must not change schema or introduce new fields.
