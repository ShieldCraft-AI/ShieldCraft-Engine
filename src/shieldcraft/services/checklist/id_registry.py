"""
Global ID registry for checklist items.
"""


class IDRegistry:
    """Registry to track and detect duplicate checklist item IDs."""

    def __init__(self):
        self.registry = {}
        self.duplicates = []

    def register(self, item_id, item=None):
        """
        Register an item ID.

        Args:
            item_id: String ID to register
            item: Optional item dict for context

        Returns:
            bool: True if successfully registered, False if duplicate
        """
        if item_id in self.registry:
            self.duplicates.append({
                "id": item_id,
                "first_occurrence": self.registry[item_id],
                "duplicate_occurrence": item
            })
            return False

        self.registry[item_id] = item
        return True

    def has_duplicates(self):
        """Check if any duplicates were found."""
        return len(self.duplicates) > 0

    def get_duplicates(self):
        """Get sorted list of duplicate entries."""
        return sorted(self.duplicates, key=lambda x: x["id"])

    def get_all_ids(self):
        """Get sorted list of all registered IDs."""
        return sorted(self.registry.keys())


def create_registry(items):
    """
    Create ID registry from list of items.

    Args:
        items: List of checklist items

    Returns:
        IDRegistry instance
    """
    registry = IDRegistry()

    for item in items:
        item_id = item.get("id")
        if item_id:
            registry.register(item_id, item)

    return registry
