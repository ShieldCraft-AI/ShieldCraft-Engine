# ShieldCraft Engine Contracts (SE v1)

This document freezes the externally visible contracts for SE v1.

1) DSL Schema
- File: `src/shieldcraft/dsl/schema/se_dsl.schema.json`
- Contract: Spec must validate against this schema for canonical or legacy formats.

2) Instruction Validation API
- Entrypoint: `shieldcraft.services.validator.validate_instruction_block(spec)`
- Behavior: Raises `ValidationError(code, message, location)` on instruction failures.
- Determinism: `ValidationError.to_dict()` is deterministic and stable.

3) Repo Sync Contract
- File: `REPO_STATE_FILENAME` constant in `shieldcraft.services.sync` (frozen).
- Entrypoint: `verify_repo_sync(repo_root)` returns dict {"ok": bool, "sha256": str, ...} or raises `SyncError`.

4) Self-host Contract
- Input: product spec (dict) passed to `Engine.run_self_host(spec, dry_run=True/False)`.
- Outputs (allowed under `.selfhost_outputs/{fingerprint}/`):
  - `bootstrap/*`, `modules/*`, `fixes/*`, `cycles/*`, `integration/*`
  - `bootstrap_manifest.json`, `manifest.json`, `summary.json`, `errors.json`
- Guarantee: Deterministic outputs and no side-effects outside the output dir.
- Enforcement: `Engine` enforces preflight (sync + validation) non-bypassably.

All contracts are now frozen; no provisional TODOs remain in runtime code (templates marked as placeholders only).
