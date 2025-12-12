import json
import pathlib


class SpecLoader:
    def load(self, path):
        p = pathlib.Path(path)
        return json.loads(p.read_text())
