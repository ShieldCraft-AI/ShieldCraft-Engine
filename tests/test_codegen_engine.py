from shieldcraft.services.codegen.generator import CodeGenerator
from shieldcraft.services.codegen.emitter.writer import FileWriter
import pathlib
import shutil


def test_codegen_outputs():
    checklist = [{
        "id": "TASK-0001",
        "ptr": "/x",
        "text": "Implement something"
    }]
    gen = CodeGenerator()
    outputs = gen.run(checklist)
    assert "TASK-0001" in outputs[0]["content"]


def test_writer_creates_files(tmp_path):
    writer = FileWriter()
    outputs = [{"path": f"{tmp_path}/test.py", "content": "x"}]
    writer.write_all(outputs)
    assert (tmp_path / "test.py").exists()
