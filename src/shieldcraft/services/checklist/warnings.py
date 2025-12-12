import json
import os


def write_warnings(product_id, warnings):
    path = f"products/{product_id}/checklist/warnings.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"warnings": warnings}, f, indent=2)
