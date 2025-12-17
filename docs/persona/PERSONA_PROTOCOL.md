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
- Purpose: Personas are bounded, auditable decision agents whose role is to surface deterministic, evidence-backed guidance and to flag unsafe or invariant-violating actions (refusal signals are advisory-only under Phase 15 non-authority lock).
- Authority classes (Phase 6 metadata):
	- DECISIVE | ADVISORY | ANNOTATIVE — **metadata-only**. These authority classifications are descriptive and do **not** by themselves grant runtime refusal authority. Under the Phase 15 persona non-authority lock, personas are advisory-only and may record annotations, diagnostics, and advisory veto signals for audit; **any** refusal authority or runtime enforcement remains the responsibility of governance and engine contracts (see `docs/governance/PERSONA_NON_AUTHORITY_CONTRACT.md`).

- Routing model: invocation is static and deterministic. An explicit routing table maps {phase} → persona set (see `src/shieldcraft/persona/routing.py`); if unset, discovery falls back to persona `scope`.

- Decision precedence: DECISIVE > ADVISORY > ANNOTATIVE (metadata-only; these classifications are informational and do not affect runtime behavior under Phase 15 persona non-authority lock).

- Event emission rules: All persona outputs MUST be recorded as PersonaEvents and PersonaAnnotations (via the observability APIs) and persisted with a deterministic companion hash for audit.

Normative rules
---------------
- Determinism: Persona outputs must be deterministic for the same inputs and repository state.
- Auditability: All persona decisions and annotations must be recorded and linkable to Persona Decision Records (PDRs; reserved for future audit extensions).
- Non-interference: Persona outputs are evidence and must not, by themselves, change canonical checklist semantics; compression for auditability is permitted (see `checklist.persona_summary`).
- Refusal: Persona vetoes are recorded and resolved deterministically for audit; under the Phase 15 non-authority lock they are advisory diagnostics (G7) and do **not** by themselves produce REFUSAL or BLOCKER outcomes. Any runtime refusal is handled by governance/engine refusal gates and contracts (see `docs/governance/REFUSAL_AUTHORITY_CONTRACT.md`). Standard advisory recording is represented by **G7_PERSONA_VETO**; **G12_PERSONA_VETO_ENFORCEMENT** is an exceptional/legacy recording used when enforcement surfaces an error during generation or enforcement and is not the default advisory flow.
- Prohibitions: Personas must not mutate engine internals, identifiers, or produce side-effects beyond recorded events and sanctioned constraints.

Change control
--------------
This document is canonical. Changes require an explicit governance decision, decision-log entry, and a phased implementation. Deprecated or legacy persona guidance is archived in `docs/persona/legacy/` and must not override this core protocol.

See also: `docs/governance/PERSONA_AUTHORITY_MODEL.md`, `docs/governance/PERSONA_PROTOCOL_DEPRECATIONS.md`.

Reader Aid — Non-Authoritative: Persona Protocol — At a Glance
-------------------------------------------------------------
- What personas are
  - Personas are **bounded, auditable decision agents** whose role is to surface deterministic, evidence-backed guidance and to flag unsafe or invariant-violating actions (refusal signals are advisory-only under Phase 15 non-authority lock).

- What personas can emit
  - **Annotations** and evidence attached to checklists or artifacts.
  - **PersonaEvents** and **PersonaAnnotations** written to observability outputs and persisted with deterministic companion hashes for audit.
  - **Diagnostics** and recorded signals for visibility (recorded as PersonaEvents).

- What personas cannot do
  - Persona outputs are **evidence-only** and **must not, by themselves, change canonical checklist semantics**.
  - Personas **MUST NOT** mutate engine internals, identifiers, or produce side-effects beyond recorded events and sanctioned constraints.
  - Persona signals **do not themselves cause REFUSAL or BLOCKER outcomes**; enforcement is governed elsewhere.

- Authority & enforcement
  - Authority metadata classes exist (DECISIVE | ADVISORY | ANNOTATIVE) and are **metadata-only**; they do not, by themselves, grant runtime refusal authority.
  - The authoritative mapping of REFUSAL authority and any runtime enforcement is the responsibility of governance and engine contracts (see `docs/governance/PERSONA_NON_AUTHORITY_CONTRACT.md` and `docs/governance/REFUSAL_AUTHORITY_CONTRACT.md`).

- Determinism & audit
  - Persona outputs **must be deterministic** for the same inputs and repository state.
  - All persona decisions and annotations **must be recorded** and linkable to Persona Decision Records (PDRs; reserved for future audit extensions) for auditability.

*This section is a reader aid and is explicitly non-authoritative; consult governance contracts for authoritative rules and enforcement.*