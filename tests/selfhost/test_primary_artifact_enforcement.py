import json
import os
import tempfile
import shutil


def test_no_primary_artifact_emits_interpreted_checklist(monkeypatch):
    """If checklist generator noop, interpreter should still emit a draft checklist."""
    from shieldcraft.main import run_self_host

    # Make the checklist generator noop so no checklist would be written by generator
    import importlib
    gen_mod = importlib.import_module('shieldcraft.services.checklist.generator')
    monkeypatch.setattr(gen_mod.ChecklistGenerator, 'build', lambda self, *a, **k: None)

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {"metadata": {"product_id": "no-primary", "self_host": True}, "invalid": True}
        json.dump(spec, tmp)
        path = tmp.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        # Should not raise; interpreter must produce a draft
        run_self_host(path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        assert os.path.exists('.selfhost_outputs/checklist_draft.json')
        cd = json.loads(open('.selfhost_outputs/checklist_draft.json').read())
        assert isinstance(cd.get('items'), list) and len(cd.get('items')) > 0
    finally:
        os.unlink(path)


def test_silence_justification_emitted_on_empty_checklist(monkeypatch):
    """If checklist is emitted but contains zero items, a justification file should be written."""
    from shieldcraft.main import run_self_host

    import importlib
    gen_mod = importlib.import_module('shieldcraft.services.checklist.generator')
    # Return an explicit empty checklist
    monkeypatch.setattr(gen_mod.ChecklistGenerator, 'build', lambda self, *a, **k: {"items": []})

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        spec = {"metadata": {"product_id": "silence-test", "self_host": True},
                "model": {"version": "1.0"}, "sections": [{"id": "core"}]}
        json.dump(spec, tmp)
        path = tmp.name

    try:
        if os.path.exists('.selfhost_outputs'):
            shutil.rmtree('.selfhost_outputs')
        # Allow dirty worktree if needed
        os.environ['SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY'] = '1'
        run_self_host(path, 'src/shieldcraft/dsl/schema/se_dsl.schema.json')
        os.environ.pop('SHIELDCRAFT_SELFBUILD_ALLOW_DIRTY', None)

        assert os.path.exists('.selfhost_outputs/checklist_draft.json')
        assert os.path.exists('.selfhost_outputs/silence_justification.json')
        with open('.selfhost_outputs/silence_justification.json') as f:
            sj = json.load(f)
        assert sj.get('item_count') == 0
    finally:
        if os.path.exists(path):
            os.unlink(path)
