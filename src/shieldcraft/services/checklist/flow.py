def compute_flow(spec):
    """
    Produces upstream/downstream relationships:
    - metadata → architecture → agents → api → outputs
    - strictly deterministic, no inference beyond structure
    """
    flows = []

    if "metadata" in spec:
        flows.append(("metadata", "architecture"))
    if "architecture" in spec:
        flows.append(("architecture", "agents"))
    if "agents" in spec:
        flows.append(("agents", "api"))
    if "api" in spec:
        flows.append(("api", "outputs"))

    return flows


def flow_tasks(flows):
    tasks = []
    for a, b in flows:
        tasks.append({
            "ptr": f"/{b}",
            "text": f"{b} depends on {a}",
            "value": {"from": a, "to": b}
        })
    return tasks
