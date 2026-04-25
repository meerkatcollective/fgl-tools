import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def run(path):
    return subprocess.run(
        [sys.executable, "-m", "fgl_validator", str(path)],
        capture_output=True,
        text=True,
    )


def test_cli_valid_exits_zero():
    r = run(FIXTURES / "valid/jersey_boys_rtf.fgl")
    assert r.returncode == 0


def test_cli_missing_terminator_exits_one():
    r = run(FIXTURES / "invalid/missing_terminator.fgl")
    assert r.returncode == 1
    assert "[FGL004]" in r.stdout
