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
    Compose from namespace, intent_category, normalized evidence hash and ptr so ids
    remain stable when those semantic inputs are unchanged.
    Format: sha256(namespace|intent|evidence_hash|ptr)[0:12]
    """
    intent = item.get("intent_category") or "misc"
    ev = item.get("evidence") or {}
    # Prefer explicit source excerpt hash when available
    excerpt = ev.get("source_excerpt_hash")
    if not excerpt:
        src = ev.get("source") or {}
        ptr = src.get("ptr") or item.get("ptr") or ""
        line = str(src.get("line") or "")
        excerpt = hashlib.sha256(f"{ptr}|{line}".encode("utf-8")).hexdigest()[:12]
    raw = f"{namespace}|{intent}|{excerpt}|{item.get('ptr') or ''}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]
