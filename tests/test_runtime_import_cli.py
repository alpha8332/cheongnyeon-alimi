from __future__ import annotations

import io
import unittest
from uuid import UUID
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
        run_writer = Mock()
        run_writer.start.return_value = UUID(
            "11111111-1111-4111-8111-111111111111"
        )
        run_writer_factory = Mock(return_value=run_writer)

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
            patch(
                "scripts.import_runtime_data.settings.SQL_ECHO",
                False,
            ),
        ):
            exit_code = main(
                ["--source", "youthcenter-api"],
                run_writer_factory=run_writer_factory,
            )

        self.assertEqual(0, exit_code)
        create_engine.assert_called_once()
        self.assertFalse(
            create_engine.call_args.kwargs["sql_echo"],
        )
        db.close.assert_called_once_with()
        engine.dispose.assert_called_once_with()
        run_writer_factory.assert_called_once_with(session_factory)
        self.assertEqual(
            "partial_failure",
            run_writer.finish.call_args.kwargs["status"],
        )

    def test_cli_reports_safe_summary_and_validation_raw_ids(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        db = Mock()
        run_writer = Mock()
        run_writer.start.return_value = UUID(
            "22222222-2222-4222-8222-222222222222"
        )

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
                run_writer_factory=Mock(return_value=run_writer),
                stdout=stdout,
                stderr=stderr,
            )

        self.assertEqual(0, exit_code)
        self.assertIn("raw=4", stdout.getvalue())
        self.assertIn("invalid=1", stdout.getvalue())
        self.assertIn("inserted=1", stdout.getvalue())
        self.assertIn("raw_document_ids=", stdout.getvalue())
        self.assertIn(
            "run_id=22222222-2222-4222-8222-222222222222",
            stdout.getvalue(),
        )
        self.assertNotIn("runtime/raw", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())
        db.close.assert_called_once_with()

    def test_cli_missing_raw_is_a_safe_failure(self) -> None:
        stderr = io.StringIO()
        db = Mock()
        run_writer = Mock()
        run_writer.start.return_value = UUID(
            "33333333-3333-4333-8333-333333333333"
        )
        with patch(
            "scripts.import_runtime_data.import_runtime_raw",
            side_effect=RuntimeReplayError(
                "no stored Raw documents found for source"
            ),
        ):
            exit_code = main(
                ["--source", "youthcenter-api"],
                session_factory=Mock(return_value=db),
                run_writer_factory=Mock(return_value=run_writer),
                stderr=stderr,
            )

        self.assertEqual(1, exit_code)
        self.assertEqual(
            "runtime import failed: "
            "no stored Raw documents found for source\n",
            stderr.getvalue(),
        )
        db.close.assert_called_once_with()
        self.assertEqual(
            "failed",
            run_writer.finish.call_args.kwargs["status"],
        )
        self.assertEqual(
            "RuntimeReplayError",
            run_writer.finish.call_args.kwargs["error_type"],
        )

    def test_unexpected_failure_does_not_expose_secret(self) -> None:
        stderr = io.StringIO()
        db = Mock()
        run_writer = Mock()
        run_writer.start.return_value = UUID(
            "44444444-4444-4444-8444-444444444444"
        )
        with patch(
            "scripts.import_runtime_data.import_runtime_raw",
            side_effect=RuntimeError("apiKeyNm=do-not-print"),
        ):
            exit_code = main(
                ["--source", "youthcenter-api"],
                session_factory=Mock(return_value=db),
                run_writer_factory=Mock(return_value=run_writer),
                stderr=stderr,
            )

        self.assertEqual(1, exit_code)
        self.assertNotIn("do-not-print", stderr.getvalue())
        self.assertIn("error_type=RuntimeError", stderr.getvalue())
        db.close.assert_called_once_with()
        self.assertEqual(
            "RuntimeError",
            run_writer.finish.call_args.kwargs["error_type"],
        )

    def test_dry_run_does_not_create_execution_history(self) -> None:
        db = Mock()
        run_writer_factory = Mock()

        with patch(
            "scripts.import_runtime_data.import_runtime_raw",
            return_value=_result(),
        ):
            exit_code = main(
                ["--source", "youthcenter-api", "--dry-run"],
                session_factory=Mock(return_value=db),
                run_writer_factory=run_writer_factory,
            )

        self.assertEqual(0, exit_code)
        run_writer_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
