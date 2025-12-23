import json
import os
import tempfile
import shutil


def test_checklist_determinism_for_same_spec():
    """Running checklist generation twice for identical spec yields identical draft bytes."""
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    from shieldcraft.services.spec.ingestion import ingest_spec

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as t:
        spec = {"metadata": {"product_id": "det-test", "version": "1.0", "spec_format": "canonical_json_v1"},
                "model": {"version": "1.0"}, "sections": [{"id": "core", "description": "core"}]}
        json.dump(spec, t)
        sp = t.name

    try:
        s = ingest_spec(sp)
        gen = ChecklistGenerator()
        c1 = gen.build(s, dry_run=True)
        # write to disk deterministically
        tmpdir = tempfile.mkdtemp()
        p1 = os.path.join(tmpdir, "checklist1.json")
        with open(p1, "w") as f:
            json.dump(c1, f, indent=2, sort_keys=True)
        # second run
        c2 = gen.build(s, dry_run=True)
        p2 = os.path.join(tmpdir, "checklist2.json")
        with open(p2, "w") as f:
            json.dump(c2, f, indent=2, sort_keys=True)

        b1 = open(p1, "rb").read()
        b2 = open(p2, "rb").read()
        assert b1 == b2, "Checklist outputs differ across identical runs"
    finally:
        if os.path.exists(sp):
            os.unlink(sp)
        shutil.rmtree(tmpdir)
