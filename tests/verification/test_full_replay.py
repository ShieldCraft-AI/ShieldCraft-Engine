import json
from shieldcraft.engine import Engine
from shieldcraft.verification.replay_engine import replay_and_compare


def test_full_run_and_replay(tmp_path):
    engine = Engine("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    spec = json.load(open("spec/se_dsl_v1.spec.json"))

    # Ensure the worktree check passes in test environments
    import shieldcraft.persona as persona_mod
    persona_mod._is_worktree_clean = lambda: True

    ast = engine.ast.build(spec)
    checklist = engine.checklist_gen.build(spec, ast=ast, engine=engine)
    det = checklist.get("_determinism")
    assert det is not None

    # Replay and expect a match
    r = replay_and_compare(engine, det)
    assert r.get("match") is True
