"""
Verification Spine package — structural scaffold only.

This module intentionally contains no imports or executable logic.
"""

__all__ = []

# Register baseline verification properties on import
try:
    from . import baseline  # noqa: F401
except Exception:
    # Import failures should not break module importers; failing imports will
    # surface during verification runtime where appropriate.
    pass
