from fgl_validator import validate


def test_returns_parse_error_for_garbage():
    diags = validate("<<<")
    assert any(d.code == "FGL000" for d in diags)


def test_clean_valid_input_no_diagnostics():
    assert validate("<F3>HELLO<p>") == []
