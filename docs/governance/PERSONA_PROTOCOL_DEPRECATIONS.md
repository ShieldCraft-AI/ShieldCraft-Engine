# Persona Protocol Deprecations (Phase 6)

This file records **deprecated** or **archived** persona protocol mechanisms identified during Phase 6 so they can be audited and retired in a future phase. No deletions are performed in this phase — this document is *informational* and *non-authoritative* about policy.

Deprecated / Archived items (facts-only):

- **Legacy persona profiles** (`docs/persona/legacy/*`)
  - Rationale: these persona profiles are subordinate to the canonical `PERSONA_PROTOCOL.md` and are retained for historical/contextual reference only.

- **Ad-hoc persona routing by phase or discovery heuristics**
  - Rationale: implicit routing is superseded by the explicit routing table implemented in `src/shieldcraft/persona/routing.py` (Phase 6 introduces a deterministic, static routing table).

- **Implicit authority inference from persona role or phase**
  - Rationale: Phase 6 introduces an explicit `authority` classification (DECISIVE|ADVISORY|ANNOTATIVE); implicit inference from role/phase is deprecated and will be considered for removal in a later phase after governance review.

Notes:

- This document is intentionally conservative: it does not remove or change any code. It only flags mechanisms that are considered for future deprecation and records the rationale and candidate replacements introduced in Phase 6.
