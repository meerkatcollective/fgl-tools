import json
from pathlib import Path

import pytest

from fgl_validator import validate

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("path", sorted((FIXTURES / "valid").glob("*.fgl")))
def test_valid(path):
    assert validate(path.read_text()) == []


@pytest.mark.parametrize("path", sorted((FIXTURES / "invalid").glob("*.fgl")))
def test_invalid(path):
    expected = json.loads(path.with_suffix(".expected.json").read_text())
    actual = [d.__dict__ for d in validate(path.read_text())]
    actual_keys = {(d["code"], d["line"]) for d in actual}
    expected_keys = {(d["code"], d["line"]) for d in expected}
    assert actual_keys == expected_keys
