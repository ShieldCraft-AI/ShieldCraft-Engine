# Copilot Instructions — ShieldCraft Engine (Authoritative Execution Contract)

- Role: Copilot operates as implementer only. All code changes and additions must be concrete implementations, not speculative or exploratory refactors.
- Execution model: All execution blocks must be JSON-only responses or file edits; no prose in the execution response. Use repository tools for collaboration and testing.
- Check-before-create: Scripts and code must verify file existence before creating new files; do not overwrite existing artifacts without explicit user approval.
- Check-before-overwrite: When modifying files, preserve existing content by creating backups (.bak) and prefer in-place edits that maintain public API compatibility.
- Single canonical DSL: The authoritative DSL is defined at `spec/schemas/se_dsl_v1.schema.json`. Do not introduce parallel DSLs, alternate schemas, or ambiguous loader paths.
- Fail-hard: On repository contract mismatches (e.g., schema path vs loader), fail with explicit errors. Do not implement compatibility layers automatically.
- Every operation: Run tests and repository tree verification prior to finalizing commits. Document any deviations in artifacts/ or .selfhost_outputs/.
- No speculative stubs: Do not add placeholder functions or TODOs as a long-term commitment. If temporary stubs are required for tests, mark them explicitly and keep short-lived.


---

This file is the authority for how Copilot is expected to act in the ShieldCraft repository. It defines enforcement points and behavior expectations. If this file conflicts with the repository's automated checks, prefer repository policies and failing tests until corrected.
