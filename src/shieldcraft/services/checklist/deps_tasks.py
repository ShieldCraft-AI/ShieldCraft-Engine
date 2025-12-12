def dependency_tasks(edges):
    tasks = []
    for frm, to in edges:
        tasks.append({
            "ptr": to,
            "text": f"{to} depends on {frm}",
            "value": {"from": frm, "to": to}
        })
    return tasks
