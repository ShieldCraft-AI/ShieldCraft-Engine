import hashlib
from shieldcraft.services.governance import map as govmap


def test_governance_mapping_files_exist_and_hash_match():
    mappings = govmap.all_mappings()
    for code, info in mappings.items():
        file = info.get("file")
        file_hash = info.get("file_hash")
        # File must exist and stored hash must match actual content
        assert file is not None, f"Mapping for {code} missing file"
        assert file_hash is not None, f"File {file} for {code} missing or unreadable"
        # Recompute and compare
        import hashlib
        with open(file, "rb") as f:
            actual = hashlib.sha256(f.read()).hexdigest()
        assert actual == file_hash
