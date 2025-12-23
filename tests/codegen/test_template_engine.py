import tempfile
from pathlib import Path
from shieldcraft.services.codegen.template_engine import TemplateEngine


def test_template_engine_load():
    te = TemplateEngine()
    template = te.load_template("basic_python.txt")
    assert template is not None
    assert isinstance(template, str)


def test_template_engine_render():
    with tempfile.TemporaryDirectory() as tmpdir:
        te = TemplateEngine()
        result = te.render("Hello {{name}}!", {"name": "World"})
        assert result == "Hello World!"


def test_template_engine_safe_write():
    with tempfile.TemporaryDirectory() as tmpdir:
        te = TemplateEngine()
        output = Path(tmpdir) / "subdir" / "output.txt"
        te.safe_write(str(output), "test content\nline2")

        assert output.exists()
        content = output.read_text()
        assert content == "test content\nline2"
        assert "\r\n" not in content
