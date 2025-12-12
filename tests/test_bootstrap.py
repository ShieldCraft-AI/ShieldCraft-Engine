"""Bootstrap test to ensure imports work correctly."""

def test_imports():
    """Test that all main modules can be imported."""
    try:
        from shieldcraft import main
        from shieldcraft.util import json_canonicalizer
        from shieldcraft.services.ast import node, builder
        from shieldcraft.services.planner import planner
        from shieldcraft.services.checklist import generator
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_main():
    """Test that main function exists."""
    from shieldcraft.main import main
    assert callable(main), "main should be a callable function"
    print("✓ main() function is callable")


def test_canonicalizer():
    """Test that canonicalize function exists."""
    from shieldcraft.util.json_canonicalizer import canonicalize
    result = canonicalize({"test": "data"})
    assert result is not None, "canonicalize should return result"
    print("✓ canonicalize function works")


def test_validator():
    """Test that SpecValidator exists."""
    from shieldcraft.services.dsl.validator import SpecValidator
    v = SpecValidator("spec/schemas/se_dsl_v1.schema.json")
    assert v is not None, "SpecValidator should instantiate"
    print("✓ SpecValidator instantiates")


def test_ast():
    """Test that AST classes exist."""
    from shieldcraft.services.ast.node import Node
    from shieldcraft.services.ast.builder import ASTBuilder
    n = Node("test")
    b = ASTBuilder()
    result = b.build({})
    assert result is not None, "ASTBuilder should return a Node"
    print("✓ AST classes instantiate")


def test_planner():
    """Test that Planner class exists."""
    from shieldcraft.services.planner.planner import Planner
    from shieldcraft.services.ast.node import Node
    p = Planner()
    result = p.plan(Node("root"))
    assert isinstance(result, list), "Planner should return a list"
    print("✓ Planner instantiates and runs")


def test_checklist():
    """Test that ChecklistGenerator class exists."""
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    g = ChecklistGenerator()
    result = g.generate([])
    assert result == [], "ChecklistGenerator should return empty list"
    print("✓ ChecklistGenerator instantiates and runs")


if __name__ == "__main__":
    print("Running bootstrap tests...\n")
    test_imports()
    test_main()
    test_canonicalizer()
    test_validator()
    test_ast()
    test_planner()
    test_checklist()
    print("\n✓ All bootstrap tests passed!")
