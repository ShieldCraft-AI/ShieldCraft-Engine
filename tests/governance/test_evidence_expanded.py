"""
Test expanded evidence bundle with additional hashes.
"""


class MockDeterminism:
    """Mock determinism service for testing."""

    def canonicalize(self, data):
        """Return canonical representation."""
        import json
        return json.dumps(data, sort_keys=True)

    def hash(self, canonical):
        """Return hash of canonical data."""
        import hashlib
        return hashlib.sha256(canonical.encode()).hexdigest()


def test_evidence_bundle_expanded_hashes():
    """Test that evidence bundle includes expanded hash fields."""
    from shieldcraft.services.governance.evidence import EvidenceBundle

    det = MockDeterminism()
    prov = {}
    bundle = EvidenceBundle(det, prov)

    checklist = [
        {"id": "item1", "ptr": "/metadata/version"},
        {"id": "item2", "ptr": "/architecture/modules"}
    ]
    invariants = [
        {"id": "inv1", "rule": "version_required"}
    ]
    graph = {
        "item1": [],
        "item2": ["item1"]
    }
    provenance = {
        "timestamp": "2024-01-01T00:00:00Z",
        "spec_version": "1.0.0"
    }

    result = bundle.build(
        checklist=checklist,
        invariants=invariants,
        graph=graph,
        provenance=provenance
    )

    # Should have all hash fields
    assert "checklist_hash" in result
    assert "items_hash" in result
    assert "manifest_hash" in result
    assert "invariants_hash" in result
    assert "dependency_graph_hash" in result

    # All hashes should be non-empty strings
    assert isinstance(result["checklist_hash"], str)
    assert len(result["checklist_hash"]) > 0
    assert isinstance(result["items_hash"], str)
    assert len(result["items_hash"]) > 0
    assert isinstance(result["invariants_hash"], str)
    assert len(result["invariants_hash"]) > 0
    assert isinstance(result["dependency_graph_hash"], str)
    assert len(result["dependency_graph_hash"]) > 0


def test_evidence_bundle_deterministic():
    """Test that evidence bundle produces deterministic hashes."""
    from shieldcraft.services.governance.evidence import EvidenceBundle

    det = MockDeterminism()
    prov = {}
    bundle = EvidenceBundle(det, prov)

    checklist = [{"id": "item1", "ptr": "/metadata/version"}]
    invariants = [{"id": "inv1", "rule": "version_required"}]
    graph = {"item1": []}
    provenance = {"timestamp": "2024-01-01T00:00:00Z"}

    # Build twice
    result1 = bundle.build(checklist=checklist, invariants=invariants, graph=graph, provenance=provenance)
    result2 = bundle.build(checklist=checklist, invariants=invariants, graph=graph, provenance=provenance)

    # Hashes should match
    assert result1["checklist_hash"] == result2["checklist_hash"]
    assert result1["items_hash"] == result2["items_hash"]
    assert result1["invariants_hash"] == result2["invariants_hash"]
    assert result1["dependency_graph_hash"] == result2["dependency_graph_hash"]
