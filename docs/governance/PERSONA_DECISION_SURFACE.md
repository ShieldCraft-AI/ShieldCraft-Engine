# Persona Decision Surface (Inventory)

This document enumerates, facts-only, the observable persona decision points, veto paths, and annotation APIs in the codebase. It is an inventory for Phase 6 work and contains no proposals.

## Key APIs

- `shieldcraft.persona.emit_veto(engine, persona_ctx, phase, code, explanation, severity)`
  - Capability: **veto** (records a veto in engine state, emits persona events/annotations)
  - Audit: writes to `engine._persona_vetoes` and emits PersonaEvent/PersonaAnnotation via observability
  - Usage: called by persona evaluation code and tests

- `shieldcraft.persona.emit_annotation(engine, persona_ctx, phase, message, severity)`
  - Capability: **annotate** (non-authoritative; emits annotations and PersonaEvent)
  - Audit: appends to engine `_persona_annotations` and emits PersonaEvent

- `shieldcraft.persona.decision_record.record_decision(engine, persona_id, phase, decision)`
  - Capability: **decision** (records non-blocking persona decisions as PersonaEvents)
  - Audit: appends to engine `_persona_decisions` and emits PersonaEvent

## Evaluation & Enforcement Points

- `shieldcraft.persona.persona_evaluator.evaluate_personas(engine, personas, items, phase="checklist")`
  - Scope: **Generator** (ChecklistGenerator.build calls this before persona-influenced checks)
  - Decision types: **veto** (emit_veto), **constraint** (non-mutating instruction recorded via `record_decision`)
  - Determinism: iterates personas deterministically by `persona.name`

- `shieldcraft.services.validator.persona_gate.enforce_persona_veto(engine)`
  - Scope: **Validator / Generator / Readiness evaluator** (called from ChecklistGenerator and readiness evaluator)
  - Decision type: **veto enforcement** (raises `RuntimeError("persona_veto:...")` when vetoes present)
  - Determinism: selects single veto deterministically (sort by severity then persona_id)

- `Engine.preflight` persona veto check
  - Scope: **Engine preflight** (top-level preflight gate checks `engine._persona_vetoes`) 
  - Decision type: **REFUSAL** (records `G7_PERSONA_VETO` event and raises `RuntimeError("persona_veto:...")`)

## Persona Loading & Discovery

- `shieldcraft.persona.load_persona(path)`
  - Scope: **persona discovery / engine self-host** (persona files loaded when persona feature enabled)
  - Decision types: **load-time errors** (raises `PersonaError` on invalid persona files, `SyncError` on repo sync failures)

- `shieldcraft.persona.persona_registry` (register/list/find_personas_for_phase)
  - Scope: **in-memory registry for deterministic test/runtime persona evaluation**
  - Behavior: `find_personas_for_phase(phase)` filters by persona `scope` (phase or `all`)

## Observability / Audit

- `shieldcraft.observability.emit_persona_event(engine, persona_id, capability, phase, payload_ref, severity)`
  - Records PersonaEvent payloads (`persona_events_v1.json`) deterministically and emits a companion hash

- `shieldcraft.observability.emit_persona_annotation(engine, persona_id, phase, message, severity)`
  - Records persona annotations (`persona_annotations_v1.json`) deterministically

## Notes (consolidation & semantics)

- Capability tokens and usage:
  - `decision` capability is used by `record_decision(...)` to record persona decisions as PersonaEvents and is exercised in tests (`tests/persona/test_decision_audit.py`). It serves as audit metadata only and does not influence runtime behavior.
  - `observe` capability (defined in `PERSONA_CAPABILITY_MATRIX`) is archived and not exercised in runtime behavior; it was reserved for future use but is no longer part of the active decision surface.

- Veto handling (normalized):
  - **Standard advisory path (G7):** `enforce_persona_veto(engine)` is the standard, deterministic advisory handling — it records a **G7_PERSONA_VETO** DIAGNOSTIC on the engine checklist context and preserves a pointer (`engine._persona_veto_selected`) for observability; it does **not** raise by default.
  - **Exceptional/legacy enforcement (G12):** `G12_PERSONA_VETO_ENFORCEMENT` is recorded and may correspond to an exception path (e.g., a generator-level RuntimeError during enforcement); this is an exceptional/legacy refusal path and not the standard advisory behavior.

## Tests and Instrumentation (examples)

- Tests call `emit_veto` and `emit_annotation` directly to simulate persona-driven vetoes and annotations
- `persona_evaluator.evaluate_personas` is exercised in generator tests (ensures constraints are recorded and applied)

## Observations (facts-only)

- Persona APIs are intentionally conservative and deterministic (sorted iteration, deterministic discovery rules).
- Persona decisions are recorded via PersonaEvent/Annotation and stored on the `engine` object for deterministic inspection.
- Veto enforcement is a deterministic, centralized check (`enforce_persona_veto`) used in multiple phases.

This completes the factual inventory of persona decision points in the current codebase.
