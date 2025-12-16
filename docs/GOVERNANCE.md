## Governance Mapping and Contracts

This file documents the deterministic governance mapping used by the engine.

Principles
- Governance rules are represented as code (data structures) under `src/shieldcraft/services/governance/map.py`.
- Each governance mapping includes:
  - `file`: path to the source document (e.g., `docs/INVARIANTS.md`)
  - `section`: human-readable section name
  - `enforcement`: `hard` | `soft` | `advisory`
  - `file_hash`: SHA-256 of the file contents (computed at import time)

Updating governance documents
- When you edit a governance doc (e.g., `docs/INVARIANTS.md`), update the corresponding entry
  in `GOVERNANCE_MAP` in `src/shieldcraft/services/governance/map.py` if you change the `file` path or section.
  The test suite will fail if a doc changes without updating the mapping (it checks file existence and hashes).

Why this exists
- Ensures policy and engine code are provably aligned and auditable.
- `file_hash` ensures a change in the prose is noticed by automated tests and review.
