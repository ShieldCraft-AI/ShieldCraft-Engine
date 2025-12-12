import hashlib


class FilePlan:
    """
    Converts checklist items into a list of file generation tasks.
    Deterministic mapping for now:
      - section → src/generated/<hash>.py
      - field   → src/generated/<hash>.py (same dir)
    """

    def build_file_plan(self, checklist):
        tasks = []
        for item in checklist:
            h = hashlib.sha256(item["id"].encode()).hexdigest()[:16]
            path = f"src/generated/{h}.py"
            tasks.append({
                "id": item["id"],
                "source": item,
                "output_path": path,
                "template_name": "basic_python"
            })
        return tasks
