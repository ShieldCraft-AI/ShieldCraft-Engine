import subprocess


def test_no_tracked_generated_files():
    """Fail the test if any files under src/generated are tracked in git."""
    res = subprocess.run(['git', 'ls-files', 'src/generated'], capture_output=True, text=True)
    files = [line for line in res.stdout.splitlines() if line.strip()]
    assert not files, f"Tracked generated files detected: {files}"
