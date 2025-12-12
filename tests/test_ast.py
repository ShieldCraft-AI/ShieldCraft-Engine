from shieldcraft.services.ast.builder import ASTBuilder


def test_ast():
    builder = ASTBuilder()
    spec = {"sections": {"s1": {"description": "d", "fields": {"a": 1}}}}
    ast = builder.build(spec)
    # New AST uses dict_entry for all dict keys
    assert ast.children[0].type == "dict_entry"
    assert ast.children[0].value["key"] == "sections"
