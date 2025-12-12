import pytest
from shieldcraft.services.artifacts.lineage import bundle
import json


def test_bundle_basic():
    spec_fp = json.dumps({"spec": "data"})
    items_fp = json.dumps({"items": []})
    plan_fp = json.dumps({"plan": []})
    code_fp = json.dumps({"code": []})
    
    result = bundle(spec_fp, items_fp, plan_fp, code_fp)
    
    assert "manifest" in result
    assert "signature" in result
    assert "paths" in result


def test_bundle_manifest_structure():
    spec_fp = json.dumps({"spec": "data"})
    items_fp = json.dumps({"items": []})
    plan_fp = json.dumps({"plan": []})
    code_fp = json.dumps({"code": []})
    
    result = bundle(spec_fp, items_fp, plan_fp, code_fp)
    
    manifest = result["manifest"]
    assert "spec_fingerprint" in manifest
    assert "items_fingerprint" in manifest
    assert "plan_fingerprint" in manifest
    assert "code_fingerprint" in manifest


def test_bundle_signature():
    spec_fp = json.dumps({"spec": "data"})
    items_fp = json.dumps({"items": []})
    plan_fp = json.dumps({"plan": []})
    code_fp = json.dumps({"code": []})
    
    result = bundle(spec_fp, items_fp, plan_fp, code_fp)
    
    # Signature should be sha256
    assert isinstance(result["signature"], str)
    assert len(result["signature"]) == 64


def test_bundle_deterministic():
    spec_fp = json.dumps({"spec": "data"}, sort_keys=True)
    items_fp = json.dumps({"items": []}, sort_keys=True)
    plan_fp = json.dumps({"plan": []}, sort_keys=True)
    code_fp = json.dumps({"code": []}, sort_keys=True)
    
    result1 = bundle(spec_fp, items_fp, plan_fp, code_fp)
    result2 = bundle(spec_fp, items_fp, plan_fp, code_fp)
    
    # Should be deterministic
    assert result1["signature"] == result2["signature"]


def test_bundle_paths():
    spec_fp = json.dumps({"spec": "data"})
    items_fp = json.dumps({"items": []})
    plan_fp = json.dumps({"plan": []})
    code_fp = json.dumps({"code": []})
    
    result = bundle(spec_fp, items_fp, plan_fp, code_fp)
    
    paths = result["paths"]
    assert "manifest" in paths
    assert "signature" in paths
    assert paths["manifest"] == "manifest.json"
    assert paths["signature"] == "manifest.sig"
