import os
import re
from typing import Dict, List


def discover_tests(root: str = "tests") -> Dict[str, str]:
    """Discover tests by scanning files under `root` and return deterministic mapping
    of stable id -> test reference string (`path::test_name`).
    """
    results: Dict[str, str] = {}
    test_func_re = re.compile(r"^def\s+(test_[a-zA-Z0-9_]+)")
    for dirpath, _, filenames in os.walk(root):
        for fn in sorted(filenames):
            if not fn.startswith("test_") or not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    m = test_func_re.match(line)
                    if m:
                        name = m.group(1)
                        ref = f"{rel}::{name}"
                        sid = f"test::{rel}::{name}"
                        results[sid] = ref
    # Return dict ordered deterministically (sorted keys)
    return dict(sorted(results.items()))
