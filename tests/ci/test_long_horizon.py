import json
from shieldcraft.engine import Engine


def test_long_horizon_self_host_repeats(monkeypatch):
    monkeypatch.setattr("shieldcraft.persona._is_worktree_clean", lambda: True)
    e = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open('spec/se_dsl_v1.spec.json'))
    previews = []
    for _ in range(3):
        p = e.run_self_host(spec, dry_run=True)
        previews.append(json.dumps(p, sort_keys=True))
    assert all(p == previews[0] for p in previews)
