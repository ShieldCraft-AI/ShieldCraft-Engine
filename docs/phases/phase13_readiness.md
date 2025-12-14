# Phase 13 Readiness (Spec Implementation)

This document summarizes the initial entry for Phase 13 (Spec Implementation) and the deterministic handoff checklist following foundation-alignment.

What to do first:
- Approve RFCs in `docs/rfc/` using `docs/rfc/approval_checklist.md`.
- Split current code/test modifications into feature PRs based on the RFC they implement (pointer map, generator-version contract, checklist normalization, bootstrap artifacts, allowed types).
- For each PR, include:
  - RFC reference and decision snapshot
  - Schema modifications (if any) as JSON Schema patches
  - Test updates and migration scripts with explicit `--lenient` CLI flags
  - CI adjustments and linter rules

Entry checklist for Phase 13:
- [ ] All RFCs have 'Yes' decisions in `docs/rfc/approval_checklist.md` or have follow-on issues
- [ ] PRs created for code/test changes; grouped per RFC
- [ ] Migration plan and CLI flags ready for pointer_map and generator_version changes
- [ ] Reviewer list assigned (product architect, platform engineer, QA)

Non-goals for Phase 13:
- No automatic rollout; changes must be approved and released by PR.
- No changes to CI gating behavior without RFC approval.

