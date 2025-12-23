import json
import os
import shutil

from scripts.run_scale_validation import run_scale


def _make_spec(path, content):
    with open(path, 'w') as f:
        json.dump(content, f)


def test_run_scale_collects_metrics_and_enforces_non_silence(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    # Good spec that will produce items
    s1 = specs / "good.json"
    _make_spec(s1, {"metadata": {"product_id": "good", "spec_format": "canonical_json_v1",
               "self_host": True}, "model": {"version": "1.0"}, "sections": [{"id": "core"}]})
    # Spec that will be invalid and produce a checklist via preview
    s2 = specs / "invalid.json"
    _make_spec(s2, {"metadata": {"product_id": "invalid", "self_host": True}, "invalid": True})

    out = tmp_path / "scale_report.json"
    artifacts = tmp_path / "artifacts"

    try:
        # Run scale validation (allow dirty to avoid worktree checks)
        report_path = run_scale(
            str(specs),
            'src/shieldcraft/dsl/schema/se_dsl.schema.json',
            out_report=str(out),
            artifacts_root=str(artifacts),
            allow_dirty=True)
        assert os.path.exists(report_path)
        r = json.loads(open(report_path).read())
        assert len(r["results"]) == 2
        for res in r["results"]:
            assert "checklist_item_count" in res
            assert "confidence_counts" in res
            assert "inferred_from_prose_count" in res
            assert "suppressed_signal_count" in res
    finally:
        # Cleanup
        if os.path.exists(str(artifacts)):
            shutil.rmtree(str(artifacts))


def test_scale_report_is_reproducible(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    s1 = specs / "one.json"
    s2 = specs / "two.json"
    _make_spec(s1, {"metadata": {"product_id": "one", "spec_format": "canonical_json_v1",
               "self_host": True}, "model": {"version": "1.0"}, "sections": [{"id": "a"}]})
    _make_spec(s2, {"metadata": {"product_id": "two", "spec_format": "canonical_json_v1",
               "self_host": True}, "model": {"version": "1.0"}, "sections": [{"id": "b"}]})

    out1 = tmp_path / "report1.json"
    out2 = tmp_path / "report2.json"
    artifacts = tmp_path / "artifacts"

    try:
        p1 = run_scale(
            str(specs),
            'src/shieldcraft/dsl/schema/se_dsl.schema.json',
            out_report=str(out1),
            artifacts_root=str(artifacts),
            allow_dirty=True)
        p2 = run_scale(
            str(specs),
            'src/shieldcraft/dsl/schema/se_dsl.schema.json',
            out_report=str(out2),
            artifacts_root=str(artifacts),
            allow_dirty=True)
        b1 = open(p1, 'rb').read()
        b2 = open(p2, 'rb').read()
        assert b1 == b2, "scale_report.json differs across runs"
    finally:
        if os.path.exists(str(artifacts)):
            shutil.rmtree(str(artifacts))
