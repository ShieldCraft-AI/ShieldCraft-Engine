**SE v1 Contract Freeze**

Date: 2025-12-15

This document records the SE v1 contract freeze.

Summary:
- The conversion state ladder is frozen: `ACCEPTED`, `CONVERTIBLE`, `STRUCTURED`, `VALID`, `READY`.
- Any change to this set requires a schema version bump and an explicit decision recorded in `docs/decision_log.md`.
- Artifact contracts, readiness gradients, and governance exports are now part of the public contract for SE v1.

Guarantees:
- `conversion_state` values are stable and emitted in `manifest.json` and `summary.json`.
- `artifact_contract_summary` will not list `guaranteed` artifacts unless `conversion_state == READY`.
- `governance_bundle.json` is a deterministic export capturing audit-relevant run state.

See `docs/CONTRACTS.md` and `docs/SE_STATE.md` for usage guidance and observability expectations.
