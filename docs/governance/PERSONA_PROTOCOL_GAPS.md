# Persona Protocol Gaps (Phase 7 audit)

This document records observed gaps between documented persona protocol language and live code (facts-only). Items below are not fixes — they are gaps to be reviewed and prioritized.

1) PERSONA_CAPABILITY_MATRIX (code) — `src/shieldcraft/persona/__init__.py`
   - Fact: code defines `PERSONA_CAPABILITY_MATRIX = {"observer": ["observe"], "auditor": ["observe","annotate"], "governance": ["observe","annotate","veto"]}`.
   - Gap: this capability matrix is not explicitly surfaced in the canonical `PERSONA_PROTOCOL.md` (CORE). Consider documenting mapping from persona roles to allowed actions.

2) Annotation rate limits (code) — `ANNOTATION_RATE_LIMIT_PER_PERSONA_PER_PHASE`
   - Fact: the system enforces deterministic per-persona per-phase annotation rate limits.
   - Gap: rate-limit behavior is operationally significant and not explicitly referenced in the core protocol.

3) Persona file resolution rules (code) — `resolve_persona_files` behavior
   - Fact: persona file selection uses version sorting and lexicographic tie-breakers.
   - Gap: selection and tie-break behavior is not described in the canonical core.

4) persona_entry decorator and entry point registry
   - Fact: `persona_entry` collects declared persona API entry points (annotate, veto).
   - Gap: the registry mechanism is operationally relevant but not referenced in the core document.

5) Persona event compression (engine)
   - Fact: Phase 6 introduced `checklist.persona_summary` compression inside `finalize_checklist` to summarize persona events.
   - Gap: While the INVARIANTS document mentions persona_summary, the core protocol may benefit from a precise line describing this audit artifact and its semantics.

6) Persona discovery fallback rules
   - Fact: routing table is optional; discovery falls back to `scope` rules implemented in `find_personas_for_phase`.
   - Gap: core doc references routing but does not enumerate the fallback behavior in detail.

Action: These gaps are documented for governance review; no code changes are included in Phase 7.
