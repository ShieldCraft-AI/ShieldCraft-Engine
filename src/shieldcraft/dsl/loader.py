import json
import pathlib
from jsonschema import validate


class DSLLoader:
    def __init__(self, schema_path):
        self.schema_path = pathlib.Path(schema_path)
        self.schema = json.loads(self.schema_path.read_text())

    def load(self, path):
        data = json.loads(pathlib.Path(path).read_text())
        validate(data, self.schema)
        return data
