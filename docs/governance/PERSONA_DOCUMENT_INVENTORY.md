# Persona Document Inventory (Phase 7)

This file is a facts-only inventory of persona-related documentation in the repository and a classification useful for Phase 7 consolidation work.

Files and classification

- CORE
  - `docs/persona/PERSONA_PROTOCOL.md` — The authoritative persona protocol (canonical core). Purpose: normative contract for persona behavior, authority, routing, event rules.

- SUPPORTING
  - `docs/persona/PERSONA_EVENTS.md` — Operational notes about persona events and PDRs; archived pointer to legacy material.
  - `docs/persona/PERSONA_ACTIVATION.md` — Activation and opt-in guidance; archived pointer to legacy material.
  - `docs/governance/PERSONA_AUTHORITY_MODEL.md` — Authoritative metadata model for persona authority classes (DECISIVE|ADVISORY|ANNOTATIVE).

- HISTORICAL
  - `docs/persona/Fiona.txt` — Persona profile example (historical/illustrative; non-authoritative).
  - `docs/persona/legacy/*` — Archived legacy persona docs preserved for historical reference.

- DEPRECATION NOTES
  - `docs/governance/PERSONA_PROTOCOL_DEPRECATIONS.md` — Marked candidate mechanisms for future removal (informational only).

Dependencies & overlaps (facts-only)

- `PERSONA_PROTOCOL.md` is the single source of truth; supporting docs are intended to reference it. Legacy docs are historical and subordinate.
- Implementation hooks & behavior to cross-check: `src/shieldcraft/persona/*`, `src/shieldcraft/persona/persona_evaluator.py`, `src/shieldcraft/persona/routing.py`, `src/shieldcraft/observability/*`.

Classification guidance (how items were classified)

- CORE: normative contract; short, prescriptive, small surface area.
- SUPPORTING: implementation or operational details that reference or explain the core.
- HISTORICAL: persona examples, legacy guides, or archived artifacts preserved for context.
- DEPRECATION: documents flagged for future removal or rewrite; preserved as an audit trail.
