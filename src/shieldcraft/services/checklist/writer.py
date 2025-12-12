class ChecklistWriter:
    def __init__(self):
        self.lines = []

    def header(self):
        self.lines.append("# ShieldCraft Engine – Generated Checklist")
        self.lines.append("")

    def section(self, key):
        from .sections import SECTION_TITLES
        title = SECTION_TITLES.get(key, key.capitalize())
        self.lines.append(f"## {title}")
        self.lines.append("")

    def task(self, item):
        tid = item["id"]
        text = item["text"]
        self.lines.append(f"- [ ] ({tid}) {text}")

    def render(self, grouped):
        self.header()
        for key, items in grouped:
            self.section(key)
            for item in items:
                self.task(item)
        return "\n".join(self.lines)
