from shieldcraft.services.ast.builder import ASTBuilder


def test_ast_builder_sorted_keys():
    builder = ASTBuilder()

    spec = {
        "z_field": "last",
        "a_field": "first",
        "m_field": "middle"
    }

    ast = builder.build(spec)

    # Verify children are in sorted order
    keys = [child.value["key"] for child in ast.children if child.type == "dict_entry"]
    assert keys == sorted(keys)


def test_ast_builder_pointers():
    builder = ASTBuilder()

    spec = {
        "metadata": {"id": "test"},
        "sections": {"sec1": {"name": "Section 1"}}
    }

    ast = builder.build(spec)

    # Root should have pointer
    assert ast.ptr == "/"

    # Check that all nodes have pointers
    for node in ast.walk():
        assert node.ptr is not None


def test_ast_builder_parent_refs():
    builder = ASTBuilder()

    spec = {
        "parent": {
            "child": "value"
        }
    }

    ast = builder.build(spec)

    # Find child node
    for node in ast.walk():
        if node.ptr == "/parent/child":
            assert hasattr(node, "parent_ptr")
            assert node.parent_ptr is not None


def test_ast_builder_collect():
    builder = ASTBuilder()

    spec = {
        "field1": "value1",
        "field2": {"nested": "value2"}
    }

    ast = builder.build(spec)

    # Collect all dict_entry nodes
    entries = builder.collect("dict_entry", ast)
    assert len(entries) > 0


def test_ast_builder_stable_arrays():
    builder = ASTBuilder()

    spec = {
        "items": [1, 2, 3]
    }

    ast = builder.build(spec)

    # Find array items
    array_nodes = [n for n in ast.walk() if n.type == "array_item"]

    # Should be in stable order
    assert len(array_nodes) == 3
    indices = [n.value["index"] for n in array_nodes]
    assert indices == [0, 1, 2]
