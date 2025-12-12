import ast, json, os

TARGET = "artifacts/dsl_field_usage.json"

# Keys accessed via obj["key"] or dict.get("key")
class FieldAccessVisitor(ast.NodeVisitor):
    def __init__(self):
        self.keys = set()

    def visit_Subscript(self, node):
        # Look for obj["field"]
        try:
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                self.keys.add(node.slice.value)
        except Exception:
            pass
        self.generic_visit(node)

    def visit_Call(self, node):
        # Look for obj.get("field")
        try:
            if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    self.keys.add(node.args[0].value)
        except Exception:
            pass
        self.generic_visit(node)

# JSON pointer fragments inside string literals
class PointerVisitor(ast.NodeVisitor):
    def __init__(self):
        self.fragments = set()

    def visit_Constant(self, node):
        if isinstance(node.value, str) and "/" in node.value:
            # heuristic: JSON pointer-ish
            if node.value.startswith("/") or "/" in node.value:
                self.fragments.add(node.value)
        self.generic_visit(node)


def scan_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
    except Exception:
        return set(), set()

    fv = FieldAccessVisitor()
    pv = PointerVisitor()
    fv.visit(tree)
    pv.visit(tree)
    return fv.keys, pv.fragments


def walk_src():
    for root, dirs, files in os.walk("src/shieldcraft"):
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


def main():
    all_keys = set()
    all_pointers = set()

    for path in walk_src():
        keys, ptrs = scan_file(path)
        all_keys.update(keys)
        all_pointers.update(ptrs)

    out = {
        "referenced_fields": sorted(all_keys),
        "json_pointer_fragments": sorted(all_pointers)
    }

    with open(TARGET, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    main()
