from shieldcraft.services.governance import map as govmap
from shieldcraft.verification.readiness_contract import REQUIRED_GATES


def test_all_strictness_rules_have_governance_mapping():
    # Iterate all rules in strictness policy RULES and ensure mapping exists
    from shieldcraft.services.spec.strictness_policy import RULES as ALL_RULES
    for lvl, rules in ALL_RULES.items():
        for r in rules:
            code = r.get("code")
            assert code is not None
            gov = govmap.get_governance_for(code)
            assert gov.get("file") is not None, f"Governance mapping missing file for rule {code}"
            assert gov.get("file_hash") is not None, f"Governance file hash missing for rule {code}"


def test_readiness_gates_have_governance_mapping():
    # Readiness gates must be mapped (except determinism_replay may be internal)
    for gate in REQUIRED_GATES:
        if gate == "determinism_replay":
            # determinism_replay is derived from internal evidence and may not have an external doc
            continue
        gov = govmap.get_governance_for(gate)
        assert gov.get("file") is not None, f"Governance mapping missing for readiness gate {gate}"
        assert gov.get("file_hash") is not None, f"Governance file hash missing for readiness gate {gate}"
