# Sync Script Usage

Run `python3 scripts/sync/generate_sync_files.py --write` from repository root to generate repo_state_sync.json, dsl_field_usage.json, shieldcraft_progress.json, and sync_report.json. Review outputs, then commit changes with message: `chore(sync): generate repo sync + audit (phase-lock)` and push to branch `sync/auto-sync-<YYYYMMDD>-<shorthash>`.
