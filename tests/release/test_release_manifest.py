from shieldcraft.release import generate_release_manifest, verify_release_manifest
import os


def test_generate_and_verify_release_manifest(tmp_path):
    # Generate manifest and verify it matches artifact hashes
    generate_release_manifest("RELEASE_MANIFEST.json")
    assert os.path.exists("RELEASE_MANIFEST.json")
    assert verify_release_manifest("RELEASE_MANIFEST.json") is True
