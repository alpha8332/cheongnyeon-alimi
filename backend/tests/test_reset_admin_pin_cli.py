from contextlib import nullcontext
from io import StringIO
from unittest.mock import Mock

import pytest

from app.cli import reset_admin_pin as cli


class _SessionFactory:
    db = object()

    @classmethod
    def begin(cls):
        return nullcontext(cls.db)


@pytest.mark.parametrize(
    "stdin_text",
    (
        "1234\n1234\n",
        "\ufeff1234\r\n1234\r\n",
    ),
)
def test_reset_pin_accepts_plain_and_utf8_bom_input(
    monkeypatch,
    capsys,
    stdin_text,
):
    reset = Mock()
    monkeypatch.setattr(cli.sys, "stdin", StringIO(stdin_text))
    monkeypatch.setattr(cli, "SessionLocal", _SessionFactory)
    monkeypatch.setattr(cli, "reset_admin_pin", reset)

    assert cli.main() == 0
    reset.assert_called_once_with(_SessionFactory.db, new_pin="1234")
    output = capsys.readouterr()
    assert "completed" in output.out
    assert output.err == ""


@pytest.mark.parametrize(
    ("stdin_text", "expected_error"),
    (
        ("12345\n12345\n", "exactly 4 digits"),
        ("1234\n4321\n", "confirmation does not match"),
    ),
)
def test_reset_pin_rejects_invalid_or_mismatched_input(
    monkeypatch,
    capsys,
    stdin_text,
    expected_error,
):
    reset = Mock()
    monkeypatch.setattr(cli.sys, "stdin", StringIO(stdin_text))
    monkeypatch.setattr(cli, "reset_admin_pin", reset)

    assert cli.main() == 2
    reset.assert_not_called()
    output = capsys.readouterr()
    assert output.out == ""
    assert expected_error in output.err

