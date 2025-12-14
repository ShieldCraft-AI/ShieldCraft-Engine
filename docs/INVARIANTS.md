# Invariant Consolidation (SE v1)

This file enumerates invariants, where they are enforced, and ensures each is enforced in a single place.

- Instruction-level invariants: enforced in `shieldcraft.services.validator` via `validate_spec_instructions`.
- Repo sync invariants: enforced in `shieldcraft.services.sync.verify_repo_sync`; errors surfaced as `SyncError`.
- Pointer coverage invariants: checked in `shieldcraft.services.spec.pointer_auditor.ensure_full_pointer_coverage` and used in `preflight`.
- Checklist invariants (must/forbid): evaluated during `ChecklistGenerator.build` via `invariants.evaluate_invariant` and `evaluate_invariant` results are attached to items; enforcement for must/forbid resides in `ChecklistGenerator`/`derived` as appropriate.
- Self-host artifact emission: enforced by `Engine.run_self_host` using `is_allowed_selfhost_path()`.

Policy: Each invariant is documented and enforced in one authoritative module; enforcement points are referenced above.
