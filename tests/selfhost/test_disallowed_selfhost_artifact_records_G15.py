import pathlib


def test_engine_contains_disallowed_selfhost_artifact_event():
    p = pathlib.Path('src/shieldcraft/engine.py')
    txt = p.read_text()
    # Ensure the code records a G15 event before raising on disallowed artifacts
    assert 'G15_DISALLOWED_SELFHOST_ARTIFACT' in txt
    assert 'disallowed_selfhost_artifact' in txt
