# SUBORDINATE DOCUMENT — Non-authoritative persona profile

This document has been moved to docs/persona/legacy/PERSONA_EVENTS.md and is subordinate to docs/persona/PERSONA_PROTOCOL.md.

**Persona Events (v1) — Audit Trail and Guarantees**

- **Model**: `PersonaEvent` = `{persona_id, capability, phase, payload_ref, severity}`. Locked schema at `src/shieldcraft/persona/persona_event_v1.schema.json` (no extra fields allowed).
- **Emission points**: emitted only on attempted annotations and vetoes. Events are append-only, written to `artifacts/persona_events_v1.json`.
- **Integrity**: a deterministic SHA256 hash of the canonicalized events array is written to `artifacts/persona_events_v1.hash` to detect tampering.
- **Ordering**: events are persisted in emission order; canonicalized representation and hash ensure deterministic ordering across repeated runs for identical inputs.
- **Non-interference**: PersonaEvents are data-only and do not change engine outputs or state. Vetoes remain a single terminal refusal path and do not modify emitted artifacts beyond audit.
- **Operational note**: Persona events are generated only when `SHIELDCRAFT_PERSONA_ENABLED=1` and written atomically with the companion hash file; missing or invalid schema causes failure to emit and is treated conservatively.

## PDRs and Persona Events Mapping

- **Persona Decision Record (PDR)**: When a persona emits an event that corresponds to a decision (annotation, veto, or recommendation), a PDR must be recorded and reference the originating persona event stored in `artifacts/persona_events_v1.json`.
- **No implied approval**: Persona events are advisory and MUST NOT be interpreted as approvals or final authorizations unless the protocol conditions in `docs/persona/PERSONA_PROTOCOL.md` (e.g., ExecutionMode and Failure Classification Gate) are satisfied and the corresponding PDR indicates authorization.
- **References**: See the Failure Classification Gate and ExecutionMode invariants in `docs/governance/INVARIANTS.md` for binding rules that govern whether persona output may be treated as authoritative.
