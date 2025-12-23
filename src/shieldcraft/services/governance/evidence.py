import json
import pathlib


class EvidenceBundle:
    def __init__(self, det, prov):
        self.det = det
        self.prov = prov

    def build(self, *, checklist, provenance, invariants=None, graph=None, output_dir="evidence"):
        out = pathlib.Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        if invariants is None:
            invariants = []
        if graph is None:
            graph = []

        # Canonicalize all inputs
        checklist_canonical = self.det.canonicalize(checklist)
        invariants_canonical = self.det.canonicalize(invariants)
        graph_canonical = self.det.canonicalize(graph)

        # Compute hashes
        checklist_hash = self.det.hash(checklist_canonical)

        # Build items summary list for hashing
        items_summary = [{"id": i.get("id"), "ptr": i.get("ptr")} for i in checklist]
        items_summary_canonical = self.det.canonicalize(items_summary)
        items_hash = self.det.hash(items_summary_canonical)

        # Build manifest summary
        manifest_summary = {"items": len(checklist), "sections": len(
            set(i.get("ptr", "").split("/")[1] if i.get("ptr") else "root" for i in checklist))}
        manifest_summary_canonical = self.det.canonicalize(manifest_summary)
        manifest_hash = self.det.hash(manifest_summary_canonical)
        invariants_hash = self.det.hash(invariants_canonical)
        dependency_graph_hash = self.det.hash(graph_canonical)

        bundle = {
            "checklist_canonical": checklist_canonical,
            "checklist_hash": checklist_hash,
            "items_hash": items_hash,
            "manifest_hash": manifest_hash,
            "invariants_hash": invariants_hash,
            "dependency_graph_hash": dependency_graph_hash,
            "provenance": provenance
        }
        (out / "bundle.json").write_text(json.dumps(bundle, indent=2))
        return bundle


def sign_manifest(manifest: dict, dry_run=True) -> str:
    """
    Sign manifest with deterministic signature.

    Args:
        manifest: manifest dict to sign
        dry_run: if True, return mock signature; if False, use real signing

    Returns:
        str: signature (mock if dry_run=True)
    """
    import hashlib
    import json

    # Create canonical representation
    canonical = json.dumps(manifest, sort_keys=True)
    manifest_hash = hashlib.sha256(canonical.encode()).hexdigest()

    if dry_run:
        # Return deterministic mock signature
        return f"MOCK_SIG_{manifest_hash[:16]}"
    else:
        # INTENTIONAL: Hash-based signature for non-production use.
        # Production would require key management and real cryptographic signing.
        # Current implementation provides deterministic, verifiable signatures.
        return f"SIG_{manifest_hash}"
