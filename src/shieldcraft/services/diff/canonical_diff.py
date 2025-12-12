import json


def canonical_dump(obj):
    return json.dumps(obj, sort_keys=True, separators=(",",":"))


def diff(a, b):
    """
    Compute deterministic diff between canonical JSON of a and b.
    Output:
    {
      "added": [...],
      "removed": [...],
      "changed": [{ptr, before, after}]
    }
    """
    ca = json.loads(canonical_dump(a))
    cb = json.loads(canonical_dump(b))

    added = []
    removed = []
    changed = []

    def walk(x, y, path=""):
        if isinstance(x, dict) and isinstance(y, dict):
            keys = sorted(set(list(x.keys()) + list(y.keys())))
            for k in keys:
                p = path + "/" + k
                if k not in x and k in y:
                    added.append({"ptr":p, "value":y[k]})
                elif k in x and k not in y:
                    removed.append({"ptr":p, "value":x[k]})
                else:
                    walk(x[k], y[k], p)
        elif isinstance(x, list) and isinstance(y, list):
            ln = max(len(x), len(y))
            for i in range(ln):
                p = path + f"/{i}"
                if i >= len(x) and i < len(y):
                    added.append({"ptr":p, "value":y[i]})
                elif i < len(x) and i >= len(y):
                    removed.append({"ptr":p, "value":x[i]})
                else:
                    walk(x[i], y[i], p)
        else:
            if x != y:
                changed.append({"ptr":path, "before":x, "after":y})

    walk(ca, cb)
    return {"added":added, "removed":removed, "changed":changed}
