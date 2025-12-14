# HISTORICAL DOCUMENT — Archived

Original location: docs/phases/phase_14_contract.md
Status: Historical archive (do not treat as active authoritative doc)

# Phase 14: Self-Hosting Validation — Contract

Phase name: self-hosting-validation

Objective

- Validate that ShieldCraft Engine (SE) can consume its own canonical specs and run the self-host pipeline deterministically.
- Verify self-host dry-run outputs (manifest, summary, generated files) are deterministic and conform to schema and governance checks.

Scope & Allowed Actions

- Allowed actions:
  - Self-host pipeline execution and dry-run validations.
  - Artifact collection and deterministic comparisons (e.g., codegen previews).
  - Preflight and governance validation, contract enforcement, and pointers coverage checks.
  - Migration guard testing flags (e.g., `SHIELDCRAFT_LENIENT_TYPES`).
  - Non-invasive verification scripts and test additions for validation only.

- Forbidden actions:
  - New features or DSL extensions.
  - Production refactoring beyond validation-focused fixes.
  - Modifying the canonical DSL schema in ways not approved by an RFC.

Determinism Requirements

- All verification runs must be deterministic across repeated runs.
- Determinism verification must include: spec fingerprint, checklist items fingerprint, codegen preview content hashes, `generators/lockfile.json` hash, and any lineage or provenance signatures.

Entry Conditions

- Phase 13 is CLOSED and all approved RFCs have implementation branches isolated.
- The `main` branch working tree is clean (no tracked file modifications under `spec/`, `src/`, or `tests/`).
- All spec changes being validated are present in RFC-specific branches (one RFC → one branch).

Exit Criteria

- Phase 14 validation must produce deterministic verification artifacts for baseline spec(s).
- Approval recorded in `docs/progress.md` and `docs/phase_14_completion.md` once all validation tasks have passed per acceptance criteria.
- No changes to canonical DSL or cross-RFC code are merged without separate RFC approval.

Governance & Exceptions

- Any change required to pass validation must follow Phase 13/Phase 14 policies and be implemented via an RFC if it alters the spec or DSL behavior.
- Bugs or minor fixes limited to validation scaffolding or test harness can be merged under Phase 14 only if they are strictly verification scaffolding and do not alter runtime behavior.

---

Status: STARTED (notified in `docs/progress.md`)
