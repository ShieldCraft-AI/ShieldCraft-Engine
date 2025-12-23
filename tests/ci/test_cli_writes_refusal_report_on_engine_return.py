import os
import json
import shutil


def _cleanup():
    if os.path.exists('.selfhost_outputs'):
        shutil.rmtree('.selfhost_outputs')


def test_cli_writes_refusal_report_when_engine_returns_refusal(monkeypatch):
    import importlib
    mod = importlib.import_module('shieldcraft.main')

    _cleanup()

    def fake_engine_runner(self, spec, dry_run=False, emit_preview=None):
        return {'checklist': {'items': [], 'refusal': True, 'refusal_reason': 'disallowed_selfhost_input'}}

    monkeypatch.setattr('shieldcraft.engine.Engine.run_self_host', fake_engine_runner)

    mod.run_self_host('spec/se_dsl_v1.spec.json', 'src/shieldcraft/dsl/schema/se_dsl.schema.json')

    p = os.path.join('.selfhost_outputs', 'refusal_report.json')
    assert os.path.exists(p)
    data = json.load(open(p, encoding='utf-8'))
    assert data['checklist']['refusal'] is True
    assert data['checklist']['refusal_reason'] == 'disallowed_selfhost_input'
