import subprocess


def test_no_tracked_generated_files():
    """Fail the test if any files under src/generated are tracked in git."""
    res = subprocess.run(['git', 'ls-files', 'src/generated'], capture_output=True, text=True)
    files = [l for l in res.stdout.splitlines() if l.strip()]
    assert not files, f"Tracked generated files detected: {files}"
