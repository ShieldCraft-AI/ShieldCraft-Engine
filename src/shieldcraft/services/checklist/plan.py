class ExecutionPlan:
    """
    Deterministic multi-pass plan:
    pass_1: structural tasks
    pass_2: invariants
    pass_3: derived tasks
    pass_4: section ordering + stable IDs
    """
    def __init__(self, raw_items):
        self.raw = raw_items
        self.pass1 = []
        self.pass2 = []
        self.pass3 = []
        self.pass4 = []

    def stage_pass1(self, items):
        # identity pass: root structural items
        self.pass1 = list(items)

    def stage_pass2(self, inv_items):
        self.pass2 = list(inv_items)

    def stage_pass3(self, derived_items):
        self.pass3 = list(derived_items)

    def stage_pass4(self, final_items):
        self.pass4 = list(final_items)

    def merged(self):
        # deterministic concatenation
        return self.pass1 + self.pass2 + self.pass3 + self.pass4
