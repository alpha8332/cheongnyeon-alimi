from unittest.mock import MagicMock, patch

import pytest

from app.cli.import_seed import main
from app.services.seed_importer import ImportIssue, ImportResult


def test_cli_prints_all_import_outcomes(capsys):
    result = ImportResult(
        total=6,
        validated=6,
        inserted=1,
        updated=1,
        unchanged=1,
        skipped=2,
        rejected=1,
        failed=1,
        issues=(
            ImportIssue(
                index=4,
                source_id="youthcenter-api",
                external_id=None,
                code="missing_external_id",
            ),
        ),
    )
    db = MagicMock()

    with (
        patch("app.cli.import_seed.SessionLocal", return_value=db),
        patch("app.cli.import_seed.import_seed_data", return_value=result),
        patch("sys.argv", ["import_seed"]),
        pytest.raises(SystemExit) as captured,
    ):
        main()

    output = capsys.readouterr().out
    assert captured.value.code == 1
    assert "Total: 6" in output
    assert "Validated: 6" in output
    assert "Inserted: 1" in output
    assert "Updated: 1" in output
    assert "Unchanged: 1" in output
    assert "Skipped: 2" in output
    assert "Rejected: 1" in output
    assert "Failed: 1" in output
    assert "code=missing_external_id" in output
    db.close.assert_called_once_with()


def test_cli_passes_dry_run_and_reports_success(capsys):
    result = ImportResult(
        total=4,
        validated=4,
        inserted=4,
        dry_run=True,
    )
    db = MagicMock()

    with (
        patch("app.cli.import_seed.SessionLocal", return_value=db),
        patch(
            "app.cli.import_seed.import_seed_data",
            return_value=result,
        ) as importer,
        patch("sys.argv", ["import_seed", "--dry-run"]),
    ):
        main()

    output = capsys.readouterr().out
    assert "[SUCCESS] Seed dry run completed." in output
    importer.assert_called_once()
    assert importer.call_args.kwargs["dry_run"] is True
    db.close.assert_called_once_with()


def test_cli_failure_does_not_print_exception_message(capsys):
    db = MagicMock()
    secret_message = (
        "postgresql://service:do-not-print@database/policies could not connect"
    )

    with (
        patch("app.cli.import_seed.SessionLocal", return_value=db),
        patch(
            "app.cli.import_seed.import_seed_data",
            side_effect=RuntimeError(secret_message),
        ),
        patch("sys.argv", ["import_seed"]),
        pytest.raises(SystemExit) as captured,
    ):
        main()

    output = capsys.readouterr().out
    assert captured.value.code == 1
    assert secret_message not in output
    assert "error_type=RuntimeError" in output
    db.close.assert_called_once_with()
