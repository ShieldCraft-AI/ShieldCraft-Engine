PERSONA_PROTOCOL.md

Version: 1.1
Status: Canonical
PERSONA_PROTOCOL.md (Authoritative)

Version: 2.0 (Phase 7 canonical core)
Status: Authoritative (CORE)
Applies to: All personas operating within ShieldCraft Engine workflows

Summary
-------
This is the single authoritative persona protocol. It defines persona purpose, authority classes, routing, decision precedence, event emission rules, and explicit prohibitions. Implementation details remain in code; this document states the normative contract.

Core concepts
-------------
- Purpose: Personas are bounded, auditable decision agents whose role is to surface deterministic, evidence-backed guidance and to refuse unsafe or invariant-violating actions.
- Authority classes (Phase 6):
	- DECISIVE — may emit vetoes that can cause REFUSAL (requires governance rationale).
	- ADVISORY — may emit BLOCKER/DIAGNOSTIC signals or non-blocking constraints.
	- ANNOTATIVE — may emit annotations and evidence-only decisions.

- Routing model: invocation is static and deterministic. An explicit routing table maps {phase} → persona set (see `src/shieldcraft/persona/routing.py`); if unset, discovery falls back to persona `scope`.

- Decision precedence: DECISIVE > ADVISORY > ANNOTATIVE. Authority metadata is currently informational; runtime enforcement requires a future governed phase.

- Event emission rules: All persona outputs MUST be recorded as PersonaEvents and PersonaAnnotations (via the observability APIs) and persisted with a deterministic companion hash for audit.

Normative rules
---------------
- Determinism: Persona outputs must be deterministic for the same inputs and repository state.
- Auditability: All persona decisions and annotations must be recorded and linkable to Persona Decision Records (PDRs).
- Non-interference: Persona outputs are evidence and must not, by themselves, change canonical checklist semantics; compression for auditability is permitted (see `checklist.persona_summary`).
- Refusal: A persona veto triggers deterministic veto enforcement paths; veto resolution is deterministic and auditable.
- Prohibitions: Personas must not mutate engine internals, identifiers, or produce side-effects beyond recorded events and sanctioned constraints.

Change control
--------------
This document is canonical. Changes require an explicit governance decision, decision-log entry, and a phased implementation. Deprecated or legacy persona guidance is archived in `docs/persona/legacy/` and must not override this core protocol.

See also: `docs/governance/PERSONA_AUTHORITY_MODEL.md`, `docs/governance/PERSONA_PROTOCOL_DEPRECATIONS.md`.