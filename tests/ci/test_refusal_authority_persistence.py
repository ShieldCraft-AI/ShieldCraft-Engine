def test_refusal_authority_map_contains_known_gates():
    from shieldcraft.services.governance.refusal_authority import REFUSAL_AUTHORITY_MAP

    known = (
        'G2_GOVERNANCE_PRESENCE_CHECK',
        'G3_REPO_SYNC_VERIFICATION',
        'G14_SELFHOST_INPUT_SANDBOX',
    )

    for g in known:
        assert g in REFUSAL_AUTHORITY_MAP
