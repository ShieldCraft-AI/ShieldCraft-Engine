# Operational Readiness (SE v1)

ShieldCraft Engine v1 is now declared operational. Key points:

- How to run:
  - Schema validation: `python -m shieldcraft.main --validate-spec spec.json --schema <schema>`
  - Self-host dry-run: `python -m shieldcraft.main --self-host spec.json` (writes `.selfhost_outputs/`)

- Guarantees:
  - Deterministic outputs across runs on the same repo/spec.
  - Non-bypassable preflight: repo sync and instruction validation are enforced before side-effects.
  - Allowed artifact emission is locked to the canonical manifest.
  - Persona subsystem: hardened and declared STABLE — opt-in only, auditable annotations/vetoes, deterministic and non-authoritative.

- Failure modes:
  - Sync mismatch raises `SyncError` and aborts with structured `errors.json` (no side-effects).
  - Validation failures raise `ValidationError` and are serialized to `errors.json` in self-host.

- Operational checks:
  - `Engine` asserts readiness of validator and sync subsystems at startup.

For full contract details see `docs/CONTRACTS.md` and `src/shieldcraft/services/selfhost/README.md`.
