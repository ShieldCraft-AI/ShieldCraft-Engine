**Snapshot Authority Modes**

- **snapshot** (default): uses the internal snapshot (`artifacts/repo_snapshot.json`) as authoritative. Validation is deterministic and strict.
- **snapshot_mandatory**: like `snapshot` but treats missing snapshot artifacts as a hard error (no fallback).
- **compare**: verify both external artifact and internal snapshot and assert parity; useful for migration verification.
- **external**: legacy external scanning. This mode is opt-in and requires `SHIELDCRAFT_ALLOW_EXTERNAL_SYNC=1`.

Set the authority via the environment variable `SHIELDCRAFT_SYNC_AUTHORITY`. External mode is deprecated and requires an explicit opt-in via `SHIELDCRAFT_ALLOW_EXTERNAL_SYNC=1`.

Migration path: run jobs in `compare` mode to verify parity across repositories and CI; when parity is established, switch to `snapshot` or `snapshot_mandatory` as desired.

Readiness marker: self-host runs assert presence of a readiness marker `SELFHOST_READY_V1` in `src/shieldcraft/services/selfhost.py` to signal that the codebase is prepared for enforced self-host runs.
