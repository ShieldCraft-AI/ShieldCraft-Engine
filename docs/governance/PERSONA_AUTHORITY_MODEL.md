# Persona Authority Model (Authoritative)

This file defines the Phase 6 **Persona Authority Model** (classification and metadata only).

Purpose: introduce a single, explicit authority class for personas to make decision authority auditable and deterministic.

## Authority classes

- `DECISIVE`
  - May cause REFUSAL outcomes by emitting vetoes (via `emit_veto`).
  - Decision-impacting; use sparingly and require explicit rationale in persona definitions.

- `ADVISORY`
  - May emit non-blocking constraints and BLOCKER-class signals (via `allowed_actions`), but cannot directly cause REFUSAL.

- `ANNOTATIVE`
  - Emit annotations and decisions recorded as evidence only. Non-authoritative for pipeline control.

## Implementation note (Phase 6)

- Personas may include an optional top-level field `authority` in their persona JSON to declare one of the above classes. This is metadata-only and does not change runtime behavior by itself.
- The codebase now supports an optional `authority` attribute on `Persona` and `PersonaContext` dataclasses to carry this metadata deterministically.
- Enforcement (mapping DECISIVE->veto permission, etc.) will be introduced in a follow-up Phase 6 runtime step after governance review.

## Auditability

- Persona authority MUST be recorded in PersonaEvents and engine-side persona decision records when decisions are emitted so that audits can reconstruct which persona class made the decision.

***

This document is authoritative for Phase 6 classification metadata and is intentionally declarative.
