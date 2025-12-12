class Planner:
    def plan(self, ast):
        tasks = []
        self._collect(ast, [], tasks)
        return tasks

    def _collect(self, node, path, tasks):
        new_path = path + [node.type]
        tasks.append({
            "type": node.type,
            "value": node.value,
            "ptr": node.ptr,
            "path": new_path
        })
        for child in node.children:
            self._collect(child, new_path, tasks)
