"""
Test template validation.
"""

import tempfile
import os


def test_template_with_tabs_detected():
    """Test that templates with tabs are detected."""
    from shieldcraft.services.codegen.template_engine import TemplateEngine

    # Create temp template with tab
    with tempfile.NamedTemporaryFile(mode='w', suffix='.j2', delete=False) as f:
        f.write("def test():\n\tpass\n")  # Tab character
        temp_path = f.name

    try:
        engine = TemplateEngine()
        result = engine.validate_template_file(temp_path)

        # Should detect tab
        assert "tabs" in str(result).lower() or not result.get("valid", True)
    finally:
        os.unlink(temp_path)


def test_template_with_trailing_spaces():
    """Test that templates with trailing spaces are detected."""
    from shieldcraft.services.codegen.template_engine import TemplateEngine

    # Create temp template with trailing space
    with tempfile.NamedTemporaryFile(mode='w', suffix='.j2', delete=False) as f:
        f.write("def test():   \n    pass\n")  # Trailing spaces
        temp_path = f.name

    try:
        engine = TemplateEngine()
        result = engine.validate_template_file(temp_path)

        # Should detect trailing spaces
        assert "trailing" in str(result).lower() or not result.get("valid", True)
    finally:
        os.unlink(temp_path)


def test_valid_template_passes():
    """Test that valid template passes validation."""
    from shieldcraft.services.codegen.template_engine import TemplateEngine

    # Create valid template
    with tempfile.NamedTemporaryFile(mode='w', suffix='.j2', delete=False) as f:
        f.write("def test():\n    pass\n")  # Clean
        temp_path = f.name

    try:
        engine = TemplateEngine()
        result = engine.validate_template_file(temp_path)

        # Should pass
        assert result.get("valid", False) is True or len(result.get("errors", [])) == 0
    finally:
        os.unlink(temp_path)
