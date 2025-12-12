# ShieldCraft Engine Spec

This folder contains canonical SE DSL v1 spec and schema. Use canonical JSON rules.

## Files

- `se_dsl_v1.spec.json` - Canonical spec for ShieldCraft Engine
- `pointer_map.json` - Task ID to JSON Pointer mapping
- `schemas/` - JSON Schema definitions

## Canonical JSON Rules

- Sort keys alphabetically
- Use 2-space indentation
- No trailing whitespace
- UTF-8 encoding
- Unix line endings (LF)

## Self-Host Dry-Run

To run self-host dry-run with bootstrap spec:

```bash
python -m src.shieldcraft.engine \
  --self-host \
  --spec examples/selfhost/bootstrap_spec.json \
  --dry-run \
  --emit-preview artifacts/selfhost_preview.json
```

To validate the generated preview:

```bash
python -c "from src.shieldcraft.services.selfhost.preview_validator import validate_preview; import json; preview = json.load(open('artifacts/selfhost_preview.json')); print(validate_preview(preview))"
```

See `ci/selfhost_dryrun.yml` for CI integration.
