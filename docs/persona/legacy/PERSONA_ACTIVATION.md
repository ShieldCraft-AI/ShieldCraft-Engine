# SUBORDINATE DOCUMENT — Non-authoritative persona profile

This document has been moved to docs/persona/legacy/PERSONA_ACTIVATION.md and is subordinate to docs/persona/PERSONA_PROTOCOL.md.

**Persona Activation Contract**

## Protocol Binding

Persona activation and behavior are governed by `docs/persona/PERSONA_PROTOCOL.md` (v1.1). Persona identities and profiles (for example, "Fiona") are subordinate to the protocol rules; any language in this document that suggests personas operate by convention or trust is superseded by `PERSONA_PROTOCOL.md`. Persona behavior MUST conform to the Failure Classification Gate and ExecutionMode rules defined therein.

- **Opt-in only**: Persona behavior is disabled by default. Use CLI flag `--enable-persona` or set `SHIELDCRAFT_PERSONA_ENABLED=1` explicitly to enable.
- **Non-authoritative**: Personas may annotate execution and emit veto signals, but they cannot generate or mutate instructions, nor change deterministic outputs.
- **Scope-bound**: Personas declare a `scope` array (e.g., `"preflight"`, `"self_host"`, `"all"`) and may only annotate or veto phases within their declared scope.
- **Auditable**: Persona annotations are written to `artifacts/persona_annotations_v1.json` and persona vetoes are reflected in `Engine` state and cause deterministic refusal with `persona_veto` error codes.
- **Deterministic resolution**: When multiple vetoes exist, they are resolved deterministically by severity (`critical`> `high`> `medium`> `low`) then lexicographically by `persona_id`.

Non-goals: personas do not modify engine state, do not propose alternative actions, and do not affect the execution ordering or outputs besides halting via veto.
