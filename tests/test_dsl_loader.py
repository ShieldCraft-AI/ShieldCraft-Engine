from shieldcraft.dsl.loader import DSLLoader
from shieldcraft.services.dsl.loader import SpecLoader
import json
import tempfile
import pathlib


def test_dsl_loader_valid():
    schema = pathlib.Path("src/shieldcraft/dsl/schema/se_dsl.schema.json")
    loader = DSLLoader(schema)
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(json.dumps({
        "metadata": {"product_id": "test", "version": "0.1", "spec_format": "canonical_json_v1"},
        "sections": {}
    }).encode())
    tmp.close()
    data = loader.load(tmp.name)
    assert data["metadata"]["product_id"] == "test"


def test_loader_reads_json():
    d = {"a": 1}
    p = pathlib.Path(tempfile.gettempdir()) / "spec.json"
    p.write_text(json.dumps(d))
    assert SpecLoader().load(str(p)) == d
