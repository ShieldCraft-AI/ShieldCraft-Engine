from shieldcraft.engine import Engine


def test_run_self_host_disallowed_input_returns_checklist(monkeypatch, tmp_path):
    engine = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')

    # Monkeypatch the is_allowed_selfhost_input to simulate disallowed input
    monkeypatch.setattr('shieldcraft.services.selfhost.is_allowed_selfhost_input', lambda spec: False)

    res = engine.run_self_host({}, dry_run=True)
    assert isinstance(res, dict)
    assert 'checklist' in res
    assert res['checklist'].get('refusal') is True
    # Ensure gate event recorded
    events = res['checklist'].get('events', [])
    assert any(ev.get('gate_id') == 'G14_SELFHOST_INPUT_SANDBOX' for ev in events)


def test_run_self_host_worktree_check_failure_returns_checklist(monkeypatch, tmp_path):
    engine = Engine('src/shieldcraft/dsl/schema/se_dsl.schema.json')

    # Simulate worktree check raising an error
    def fake_is_worktree_clean():
        raise RuntimeError('git not found')

    monkeypatch.setattr('shieldcraft.persona._is_worktree_clean', fake_is_worktree_clean)

    # Run in isolated tmp dir to avoid writing into repo
    monkeypatch.chdir(tmp_path)

    res = engine.run_self_host({}, dry_run=False)
    assert isinstance(res, dict)
    assert 'checklist' in res
    events = res['checklist'].get('events', [])
    # Expect at least a self-host related event to be present
    assert any(ev.get('gate_id', '').startswith('G14_SELFHOST') for ev in events)
