from shieldcraft.services.planner.planner import Planner
from shieldcraft.services.ast.node import Node


def test_planner():
    node = Node("root")
    child = node.add(Node("section"))
    plan = Planner().plan(node)
    assert len(plan) == 2
