from shieldcraft.services.ast.builder import ASTBuilder
from shieldcraft.services.ast.node import Node


def test_node_find():
    builder = ASTBuilder()

    spec = {
        "metadata": {"id": "test"},
        "sections": {"sec1": {"name": "Section 1"}}
    }

    ast = builder.build(spec)

    # Find by pointer
    node = ast.find("/metadata")
    assert node is not None
    assert "/metadata" in node.ptr


def test_node_find_all():
    node = Node("root", ptr="/")

    child1 = Node("entry", {"key": "name", "value": "test"}, ptr="/child1")
    child2 = Node("entry", {"key": "name", "value": "test2"}, ptr="/child2")

    node.add(child1)
    node.add(child2)

    # Find all nodes with 'key' in value
    results = node.find_all("key")
    assert len(results) == 2


def test_node_walk():
    builder = ASTBuilder()

    spec = {
        "a": {"b": {"c": "value"}}
    }

    ast = builder.build(spec)

    # Walk should yield all nodes
    nodes = list(ast.walk())
    assert len(nodes) > 0
    assert ast in nodes


def test_node_to_json():
    node = Node("root", {"test": "value"}, ptr="/")
    child = Node("child", "data", ptr="/child")
    node.add(child)

    # Non-canonical
    result = node.to_json(canonical=False)
    assert result["type"] == "root"
    assert result["ptr"] == "/"
    assert len(result["children"]) == 1


def test_node_to_json_canonical():
    node = Node("root", {"test": "value"}, ptr="/")

    # Canonical should return string
    result = node.to_json(canonical=True)
    assert isinstance(result, str)


def test_node_walk_order():
    builder = ASTBuilder()

    spec = {
        "z": "last",
        "a": "first",
        "m": "middle"
    }

    ast = builder.build(spec)

    # Walk should visit in deterministic order
    ptrs1 = [n.ptr for n in ast.walk()]
    ptrs2 = [n.ptr for n in ast.walk()]

    assert ptrs1 == ptrs2  # Deterministic
