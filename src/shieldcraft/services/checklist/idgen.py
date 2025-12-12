import hashlib


def stable_id(ptr: str, text: str) -> str:
    """
    Deterministic task ID.
    ptr + text -> SHA1 truncated to 8 chars.
    """
    h = hashlib.sha1(f"{ptr}|{text}".encode()).hexdigest()
    return h[:8]


def synthesize_id(item, namespace="default"):
    """
    Deterministic ID with namespace salt.
    sha256(namespace + '|' + ptr + '|' + text)[0:12]
    """
    raw = f"{namespace}|{item['ptr']}|{item['text']}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]
