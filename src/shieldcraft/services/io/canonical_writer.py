import json


def write_canonical_json(path, data):
    """
    Write Canonical JSON:
    - UTF-8
    - sorted keys
    - no extra whitespace
    - LF only
    """
    text = json.dumps(data, sort_keys=True, separators=(",",":"))
    with open(path,"w",encoding="utf-8",newline="\n") as f:
        f.write(text)
