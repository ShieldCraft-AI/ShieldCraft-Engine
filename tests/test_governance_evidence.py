from shieldcraft.services.governance.evidence import EvidenceBundle
from shieldcraft.services.governance.determinism import DeterminismEngine
from shieldcraft.services.governance.provenance import ProvenanceEngine


def test_evidence(tmp_path):
    det = DeterminismEngine()
    prov = ProvenanceEngine()
    e = EvidenceBundle(det, prov)
    checklist = [{"id": "X", "ptr": "/x", "text": "y"}]
    b = e.build(checklist=checklist, provenance={"a": 1}, output_dir=tmp_path)
    assert "checklist_hash" in b
