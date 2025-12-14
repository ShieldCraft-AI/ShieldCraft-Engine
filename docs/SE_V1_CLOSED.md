SE v1: CLOSED

Status: SE v1 is declared CLOSED, OPERATIONAL, and SELF-HOST VERIFIED.

Highlights:
- Deterministic snapshot authority is the default (`snapshot`).
- External scanning is opt-in and deprecated (`SHIELDCRAFT_ALLOW_EXTERNAL_SYNC=1`).
- Self-host closed-loop: self-host emits a canonical `repo_snapshot.json` enabling parity checks and reproducible builds.
- CI enforces self-host smoke, self-host determinism, and a reproducibility job that runs the pipeline twice and diffs outputs.

See `docs/OPERATIONAL_READINESS.md` and `ci/selfhost_dryrun.yml` for details.
