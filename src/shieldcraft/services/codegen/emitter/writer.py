import pathlib


class FileWriter:
    def write_all(self, outputs):
        for item in outputs:
            p = pathlib.Path(item["path"])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(item["content"])
