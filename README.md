# ShieldCraft Engine

A spec-driven code generation engine with deterministic output and complete traceability.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -q

# Or use test wrapper
./scripts/run_tests.sh
```

## CI/CD

CI workflow location: `.github/workflows/spec-pipeline.yml`

The CI pipeline:
- Runs full test suite
- Validates generator lockfile version
- Checks spec determinism
- Uploads test failure artifacts

## Testing

```bash
# Run all tests
pytest -q

# Run specific test file
pytest tests/spec/test_schema_compliance.py -v

# Run with test wrapper (writes summary to artifacts/)
./scripts/run_tests.sh
```

## Architecture

- **Spec DSL**: JSON-based product specification format
- **AST Builder**: Constructs abstract syntax tree from specs
- **Checklist Generator**: Produces task checklists with lineage tracking
- **Code Generator**: Template-based code emission with traceability
- **Self-Host Mode**: Engine can generate its own components

## Development

See `docs/` for detailed documentation.

## Self-Host Dry-Run

To run self-host dry-run with the canonical spec:

```bash
python -m src.shieldcraft.engine --spec spec/se_dsl_v1.spec.json --dry-run
```

This generates a preview without writing files, useful for CI validation.

To emit a preview JSON file during self-host:

```bash
python -m shieldcraft.main --self-host spec/se_dsl_v1.spec.json --dry-run --emit-preview preview.json
```

This runs self-host in dry-run mode and writes the preview to `preview.json`. The file is not emitted without --emit-preview.

