import hashlib


def digest_bytes(data: bytes) -> str:
    """
    Compute SHA256 hex digest of bytes.
    
    Args:
        data: Raw bytes to hash
        
    Returns:
        SHA256 hex digest string
    """
    return hashlib.sha256(data).hexdigest()


def digest_text(text: str, encoding='utf-8') -> str:
    """
    Compute SHA256 hex digest of text with canonicalized newlines.
    
    Args:
        text: Text string to hash
        encoding: Text encoding (default utf-8)
        
    Returns:
        SHA256 hex digest string
    """
    # Canonicalize newlines to LF
    canonical_text = text.replace('\r\n', '\n').replace('\r', '\n')
    return digest_bytes(canonical_text.encode(encoding))
