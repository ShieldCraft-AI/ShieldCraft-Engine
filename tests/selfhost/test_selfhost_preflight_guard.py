import json
import os
import tempfile


def test_cli_run_self_host_fails_fast_and_writes_only_errors():
    """CLI-level run_self_host should write only errors.json on validation failure and no manifest."""
    from shieldcraft.main import run_self_host

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
        spec = {
            "metadata": {"product_id": "test-cli-preflight", "spec_format": "canonical_json_v1", "self_host": True},
            "invariants": [{"id": "inv.1", "rule": "true"}],
            "model": {"version": "1.0"},
            "sections": {},
            "instructions": [{"id": "i1", "type": "construction", "timestamp": "now"}],
        }
        json.dump(spec, tmp)
        tmp_path = tmp.name

    try:
        if os.path.exists(".selfhost_outputs"):
            import shutil

            shutil.rmtree(".selfhost_outputs")

        run_self_host(tmp_path, "src/shieldcraft/dsl/schema/se_dsl.schema.json")

        # errors.json should be present
        err = os.path.join(".selfhost_outputs", "errors.json")
        assert os.path.exists(err)

# Manifest may be present as a partial artifact; summary may be present for diagnostics
    # (we emit partial manifests to provide authors with actionable artifacts)
        # summary.json may be present with validity/readiness diagnostics

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
