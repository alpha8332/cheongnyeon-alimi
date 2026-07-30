"""Replay stored Runtime Raw into the configured Backend database."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TextIO


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.config import settings  # noqa: E402
from app.core.database import (  # noqa: E402
    create_db_engine,
    create_session_factory,
)
from app.services.runtime_importer import (  # noqa: E402
    RuntimeImportResult,
    import_runtime_raw,
)
from collectors.runtime import (  # noqa: E402
    SUPPORTED_SOURCE_IDS,
    RuntimeReplayError,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Replay stored Runtime Raw without calling an external API."
        )
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=SUPPORTED_SOURCE_IDS,
        help="source ID to replay",
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("runtime/raw"),
        help="stored Raw root (default: runtime/raw)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="maximum latest-batch list items, from 1 to 500",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and project database changes, then roll them back",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    session_factory: Callable[[], Any] | None = None,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    args = build_parser().parse_args(argv)
    if not 1 <= args.limit <= 500:
        print(
            "runtime import failed: limit must be from 1 to 500",
            file=stderr,
        )
        return 2

    owned_engine = None
    db = None
    try:
        selected_session_factory = session_factory
        if selected_session_factory is None:
            owned_engine = create_db_engine(
                settings.DATABASE_URL,
                environment="runtime-import",
            )
            selected_session_factory = create_session_factory(owned_engine)
        db = selected_session_factory()
        result = import_runtime_raw(
            db,
            raw_root=args.raw_root,
            source_id=args.source,
            limit=args.limit,
            dry_run=args.dry_run,
        )
    except RuntimeReplayError as exc:
        print(f"runtime import failed: {exc}", file=stderr)
        return 1
    except Exception as exc:
        print(
            "runtime import failed unexpectedly: "
            f"source={args.source} error_type={type(exc).__name__}",
            file=stderr,
        )
        return 1
    finally:
        if db is not None:
            db.close()
        if owned_engine is not None:
            owned_engine.dispose()

    _print_summary(result, stdout=stdout)
    _print_issues(result, stdout=stdout)
    if (
        result.database.skipped
        or result.database.rejected
        or result.database.failed
    ):
        return 1
    return 0


def _print_summary(
    result: RuntimeImportResult,
    *,
    stdout: TextIO,
) -> None:
    replay = result.replay
    database = result.database
    action = "dry-run" if database.dry_run else "import"
    print(
        "runtime "
        f"{action} completed: "
        f"source={replay.source_id} "
        f"raw={replay.raw_document_count} "
        f"extracted={replay.extracted_count} "
        f"valid={replay.valid_count} "
        f"partial={replay.partial_count} "
        f"invalid={replay.invalid_count} "
        f"accepted={replay.accepted_count} "
        f"inserted={database.inserted} "
        f"updated={database.updated} "
        f"unchanged={database.unchanged} "
        f"skipped={database.skipped} "
        f"rejected={database.rejected} "
        f"failed={database.failed}",
        file=stdout,
    )


def _print_issues(
    result: RuntimeImportResult,
    *,
    stdout: TextIO,
) -> None:
    for issue in result.replay.issues:
        print(
            "runtime validation issue: "
            f"index={issue.index} "
            f"source_id={issue.source_id} "
            f"external_id={issue.external_id} "
            f"codes={','.join(issue.codes)} "
            f"paths={','.join(issue.paths)} "
            f"raw_document_ids={','.join(issue.raw_document_ids)}",
            file=stdout,
        )
    programs_by_identity = {
        (program["source_id"], program["external_id"]): program
        for program in result.replay.programs
    }
    for issue in result.database.issues:
        program = programs_by_identity.get(
            (issue.source_id, issue.external_id)
        )
        raw_document_ids = (
            _program_raw_document_ids(program)
            if program is not None
            else ()
        )
        print(
            "runtime database issue: "
            f"index={issue.index} "
            f"source_id={issue.source_id} "
            f"external_id={issue.external_id} "
            f"code={issue.code} "
            f"path={issue.path} "
            f"error_type={issue.error_type} "
            f"raw_document_ids={','.join(raw_document_ids)}",
            file=stdout,
        )


def _program_raw_document_ids(
    program: dict[str, Any],
) -> tuple[str, ...]:
    return tuple(
        item["raw_document_id"]
        for item in program["provenance"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
