Snapshot feature (internal)
===========================

Purpose
-------
Provide a deterministic, internal snapshot of the repository tree to support
future enforcement workflows. This is intentionally minimal and offline-only.

Contract
--------
- Manifest `v1` contains `files` (path+sha256) and `tree_hash` (sha256 of "path:sha256" concatenation).
- Default snapshot location: `artifacts/repo_snapshot.json`.
- Default excludes: `.git`, `.venv`, `node_modules`, `artifacts/`, `.selfhost_outputs/`.

Non-goals
--------
- This is not a remote attestation; it makes no network calls.
- It does not change runtime behavior unless explicitly enabled via
  `SHIELDCRAFT_SNAPSHOT_ENABLED=1`.
