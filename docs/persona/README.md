# Persona Documentation — Canonical Entry Point

This page is the single README and index for persona-related documentation. It lists the canonical persona documents and points to archived historical materials.

Canonical documents (active)

- `docs/persona/PERSONA_PROTOCOL.md` — **Persona Protocol (Authoritative)**: normative contract describing persona purpose, routing, event emission rules, non-interference, and change control.
- `docs/governance/PERSONA_NON_AUTHORITY_CONTRACT.md` — **Persona Non-Authority Contract (Authoritative)**: Phase 15 lock; personas are advisory-only and must not cause REFUSAL/BLOCKER outcomes.
- `docs/governance/PERSONA_DECISION_SURFACE.md` — **Persona Decision Surface (Supporting Inventory)**: facts-only inventory of persona emission points, schemas, artifacts, and tests.

Statement

- Personas are **advisory-only** (Phase 15 locked). Persona outputs are annotations, diagnostics, and advisory signals only; they do not themselves change canonical checklist semantics. For authoritative enforcement rules, consult `docs/governance/PERSONA_NON_AUTHORITY_CONTRACT.md` and `docs/governance/REFUSAL_AUTHORITY_CONTRACT.md`.

Legacy & Archive (read-only, non-authoritative)

- Historical persona files and legacy profiles have been archived to `docs/archive/persona/` and are preserved for traceability. These documents are non-authoritative and exist for historical context only.

---

If you are updating persona documentation, consult the canonical documents above and avoid adding normative language to archived or legacy files.
