# Phase 13 PR Structure

This document defines the non-interactive, deterministic PR structure for implementing each approved RFC during Phase 13.

Rules (must be applied to every PR):
- Exactly one RFC per PR.
- PR title format: `RFC: <rfc-file-name> — <short description>`
- PR description must include: RFC reference link, decision excerpt from `docs/decision_log.md`, and a link to corresponding entry in `docs/implementation_plan.md`.
- The first commit in a PR MUST contain only schema/spec changes (ex: `se_dsl_v1.schema.json` updates, pointer_map schema updates) and docs updates describing the change.
- Subsequent commits in the PR MAY contain code changes implementing the spec and corresponding tests.
- Tests MUST be added or updated in the same PR as code changes, in a separate commit that follows exactly after the code changes commit.
- Migration scripts and linter rules MUST be included in a dedicated commit after tests and must be clearly labeled (e.g., `migration: add pointer_map migration script`).
- PR must include a `Migration Checklist` in the PR description, listing expected migration steps and a `rollback` section.
- No scope beyond approved RFC: PRs must not implement any unapproved feature or change unrelated to the RFC.
- Reviewers: Assign product architect and two engineers (one backend, one QA).
- PR labels:
  - `rfc/approved` - for PRs implementing an approved RFC
  - `migration` - if the PR includes migration scripts
  - `breaking` - if the PR requires behavior changes flagged as breaking (must be used sparingly)

PR Ordering and Gate:
- PR-1 (generator_version lockfile) must be merged before PR-2.
- PR-2 (allowed checklist types) must be merged before PR-3.
- PR-3 (pointer_map) must be merged before PR-4.
- PR-4 (checklist pointer normalization) must be merged before PR-5.
- PR merging is strictly gated: all PRs must reference a Jira or issue tracking ticket created by the product team; acceptance includes passing CI and QA sign-off.

Notes:
- This PR structure enforces stepwise, reviewable changes, ensuring schema updates are first and code/test follow an auditable trail.
- Any emergency deviation must be explicitly approved by product and operations.

