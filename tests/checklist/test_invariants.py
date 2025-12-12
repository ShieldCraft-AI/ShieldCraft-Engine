from shieldcraft.services.checklist.invariants import extract_invariants


def test_extract_invariants_empty():
    spec = {"metadata": {"name": "test"}}
    result = extract_invariants(spec)
    assert result == []


def test_extract_invariants_single():
    spec = {
        "rules": {
            "rule1": {
                "invariant": "x > 0"
            }
        }
    }
    result = extract_invariants(spec)
    assert len(result) == 1
    assert result[0]["pointer"] == "/rules/rule1"
    assert result[0]["type"] == "invariant"
    assert result[0]["constraint"] == "x > 0"
    assert result[0]["severity"] == "error"


def test_extract_invariants_sorted():
    spec = {
        "z": {"invariant": "z_check"},
        "a": {"invariant": "a_check"}
    }
    result = extract_invariants(spec)
    assert len(result) == 2
    assert result[0]["pointer"] == "/a"
    assert result[1]["pointer"] == "/z"
