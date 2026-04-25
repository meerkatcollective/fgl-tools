from pathlib import Path
import pytest
from fgl_validator.parser import parser

VALID = Path(__file__).parent / "fixtures/valid"

@pytest.mark.parametrize("path", sorted(VALID.glob("*.fgl")))
def test_parses_without_exception(path):
    parser.parse(path.read_text())
