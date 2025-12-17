# Persona Document Inventory (Phase 7)

This file is a facts-only inventory of persona-related documentation in the repository and a classification useful for Phase 7 consolidation work.

Files and classification

- CANONICAL (active)
  - `docs/persona/PERSONA_PROTOCOL.md` — **Persona Protocol (Authoritative)**: the single authoritative protocol for persona behavior, routing, event emission rules, and non-interference.
  - `docs/governance/PERSONA_NON_AUTHORITY_CONTRACT.md` — **Persona Non-Authority Contract (Authoritative)**: Phase 15 lock — personas are advisory-only and must not cause REFUSAL/BLOCKER outcomes.
  - `docs/governance/PERSONA_DECISION_SURFACE.md` — **Persona Decision Surface (Facts-only Inventory)**: canonical, facts-only inventory of persona emission points, schema references, and observability paths.

- SUPPORTING (metadata / informational)
  - `docs/governance/PERSONA_AUTHORITY_MODEL.md` — Authoritative metadata model for persona authority classes (DECISIVE|ADVISORY|ANNOTATIVE). **Metadata-only**: does not grant runtime refusal authority.

- ARCHIVED (historical, non-authoritative)
  - `docs/persona/PERSONA_EVENTS.md` — Archived operational notes about persona events and PDRs.
  - `docs/persona/PERSONA_ACTIVATION.md` — Archived activation and opt-in guidance.
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
