# Self-host pipeline

This module defines the self-hosting contract for ShieldCraft Engine.

Contract (high level):
- Input: product spec dict (canonicalized) with `metadata.self_host` recommended
- Output: deterministic artifacts written under `.selfhost_outputs/{fingerprint}/`
- Allowed artifacts (relative to fingerprint dir):
  - `bootstrap/*` (bootstrap modules and files)
  - `modules/*` (generated module files)
  - `fixes/*`, `cycles/*`, `integration/*` (task-derived outputs)
  - `bootstrap_manifest.json`, `manifest.json`, `summary.json`, `errors.json`
- Determinism: multiple runs on unchanged repo/spec must produce identical artifact lists and content
- Non-bypassable: preflight gates (repo sync and instruction validation) are executed before any side-effects

See `src/shieldcraft/services/selfhost/__init__.py` for the allowed artifact prefixes and helpers.
