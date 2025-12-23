class ChecklistVerifier:
    REQUIRED_FIELDS = ["id", "ptr", "text"]

    def verify(self, checklist):
        errors = []
        for item in checklist:
            for f in self.REQUIRED_FIELDS:
                if f not in item:
                    errors.append({"item": item.get("id"), "missing": f})

        # Verify resolution chains if present
        if isinstance(checklist, dict) and "resolution_chains" in checklist:
            from shieldcraft.services.checklist.resolution_chain import verify_chains
            chain_result = verify_chains(checklist["resolution_chains"])
            if not chain_result["ok"]:
                for violation in chain_result["violations"]:
                    errors.append({
                        "item": violation["item_id"],
                        "issue": violation["issue"],
                        "type": "resolution_chain"
                    })

        # Verify ancestry if present in items
        if isinstance(checklist, list):
            from shieldcraft.services.checklist.ancestry import build_ancestry, verify_ancestry
            ancestry = build_ancestry(checklist)
            ancestry_result = verify_ancestry(ancestry)
            if not ancestry_result["ok"]:
                for violation in ancestry_result["violations"]:
                    errors.append({
                        "item": violation["item_id"],
                        "issue": violation["issue"],
                        "type": "ancestry"
                    })

        # Check for duplicate IDs
        if isinstance(checklist, list):
            from shieldcraft.services.checklist.id_registry import create_registry
            registry = create_registry(checklist)
            if registry.has_duplicates():
                for dup in registry.get_duplicates():
                    errors.append({
                        "item": dup["id"],
                        "issue": "duplicate_id",
                        "type": "id_collision"
                    })

        return errors
