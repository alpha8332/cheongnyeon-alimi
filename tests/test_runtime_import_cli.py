from __future__ import annotations

import io
import unittest
from unittest.mock import Mock, patch

from scripts.import_runtime_data import main

from app.services.runtime_importer import RuntimeImportResult
from app.services.seed_importer import ImportResult
from collectors.runtime import (
    RuntimeReplayError,
    RuntimeReplayResult,
    RuntimeValidationIssue,
)


def _result() -> RuntimeImportResult:
    replay = RuntimeReplayResult(
        source_id="youthcenter-api",
        raw_document_count=4,
        extracted_count=3,
        valid_count=2,
        partial_count=0,
        invalid_count=1,
        programs=(
            {
                "source_id": "youthcenter-api",
                "external_id": "SYN-YOUTH-001",
                "provenance": [
                    {"raw_document_id": "1" * 32},
                ],
            },
        ),
        issues=(
            RuntimeValidationIssue(
                index=2,
                source_id="youthcenter-api",
                external_id="SYN-YOUTH-REJECTED",
                codes=("schema_type",),
                paths=("$.title",),
                raw_document_ids=("2" * 32, "3" * 32),
            ),
        ),
    )
    database = ImportResult(
        total=1,
        validated=1,
        inserted=1,
        committed=True,
    )
    return RuntimeImportResult(replay=replay, database=database)


class RuntimeImportCliTests(unittest.TestCase):
    def test_cli_owns_a_non_echo_database_engine_by_default(self) -> None:
        engine = Mock()
        db = Mock()
        session_factory = Mock(return_value=db)

        with (
            patch(
                "scripts.import_runtime_data.create_db_engine",
                return_value=engine,
            ) as create_engine,
            patch(
                "scripts.import_runtime_data.create_session_factory",
                return_value=session_factory,
            ),
            patch(
                "scripts.import_runtime_data.import_runtime_raw",
                return_value=_result(),
            ),
        ):
            exit_code = main(["--source", "youthcenter-api"])

        self.assertEqual(0, exit_code)
        create_engine.assert_called_once()
        self.assertEqual(
            "runtime-import",
            create_engine.call_args.kwargs["environment"],
        )
        db.close.assert_called_once_with()
        engine.dispose.assert_called_once_with()

    def test_cli_reports_safe_summary_and_validation_raw_ids(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        db = Mock()

        with patch(
            "scripts.import_runtime_data.import_runtime_raw",
            return_value=_result(),
        ):
            exit_code = main(
                [
                    "--source",
                    "youthcenter-api",
                    "--raw-root",
                    "runtime/raw",
                    "--limit",
                    "10",
                ],
                session_factory=Mock(return_value=db),
                stdout=stdout,
                stderr=stderr,
            )

        self.assertEqual(0, exit_code)
        self.assertIn("raw=4", stdout.getvalue())
        self.assertIn("invalid=1", stdout.getvalue())
        self.assertIn("inserted=1", stdout.getvalue())
        self.assertIn("raw_document_ids=", stdout.getvalue())
        self.assertNotIn("runtime/raw", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())
        db.close.assert_called_once_with()

    def test_cli_missing_raw_is_a_safe_failure(self) -> None:
        stderr = io.StringIO()
        db = Mock()
        with patch(
            "scripts.import_runtime_data.import_runtime_raw",
            side_effect=RuntimeReplayError(
                "no stored Raw documents found for source"
            ),
        ):
            exit_code = main(
                ["--source", "youthcenter-api"],
                session_factory=Mock(return_value=db),
                stderr=stderr,
            )

        self.assertEqual(1, exit_code)
        self.assertEqual(
            "runtime import failed: "
            "no stored Raw documents found for source\n",
            stderr.getvalue(),
        )
        db.close.assert_called_once_with()

    def test_unexpected_failure_does_not_expose_secret(self) -> None:
        stderr = io.StringIO()
        db = Mock()
        with patch(
            "scripts.import_runtime_data.import_runtime_raw",
            side_effect=RuntimeError("apiKeyNm=do-not-print"),
        ):
            exit_code = main(
                ["--source", "youthcenter-api"],
                session_factory=Mock(return_value=db),
                stderr=stderr,
            )

        self.assertEqual(1, exit_code)
        self.assertNotIn("do-not-print", stderr.getvalue())
        self.assertIn("error_type=RuntimeError", stderr.getvalue())
        db.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
