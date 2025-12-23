import os
import json
import ast

TARGET_FILE = "artifacts/dsl_field_usage.json"


def extract_keys_from_dict_nodes(node):
    keys = []
    if isinstance(node, ast.Dict):
        for k in node.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                keys.append(k.value)
    return keys


def walk_file(path):
    keys = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
        for n in ast.walk(tree):
            keys.extend(extract_keys_from_dict_nodes(n))
    except Exception:
        pass
    return keys


def list_python_files():
    result = []
    for root, dirs, files in os.walk("src/shieldcraft"):
        for f in files:
            if f.endswith(".py"):
                result.append(os.path.join(root, f))
    return result


def main():
    files = list_python_files()
    ast_fields = set()
    checklist_fields = set()
    raw_access = set()

    for path in files:
        keys = walk_file(path)
        if "checklist" in path:
            for k in keys:
                checklist_fields.add(k)
        else:
            for k in keys:
                ast_fields.add(k)

        # detect ANY `raw["x"]` access
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            for line in content.splitlines():
                line = line.strip()
                if "raw[" in line:
                    raw_access.add(line)
        except Exception:
            pass

    final = {
        "ast_referenced_fields": sorted(list(ast_fields)),
        "checklist_referenced_fields": sorted(list(checklist_fields)),
        "raw_access_patterns": sorted(list(raw_access))
    }

    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2)


if __name__ == "__main__":
    main()
