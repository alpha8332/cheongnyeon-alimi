"""Persist one validated RYP6 Browser detail batch as replayable Raw."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.extracted import ExtractionError  # noqa: E402
from collectors.regional_expansion import (  # noqa: E402
    RegionalBatchCheckpoint,
    RegionalBrowserCaptureStore,
    RegionalCheckpointStore,
)
from collectors.storage import RawDocumentStore  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("--raw-root", type=Path, default=Path("runtime/raw"))
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=Path("runtime/decisions/regional-checkpoints"),
    )
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        value: Any = json.loads(args.capture.read_text(encoding="utf-8"))
        captures = value if isinstance(value, list) else [value]
        if not captures or not all(isinstance(item, dict) for item in captures):
            raise ExtractionError("Browser capture root must be an object or list")
        checkpoint_store = RegionalCheckpointStore(args.checkpoint_root)
        planned: dict[str, RegionalBatchCheckpoint] = {}
        operations = []
        for capture in captures:
            source_id = capture.get("source_id")
            if not isinstance(source_id, str):
                raise ExtractionError("Browser capture source_id is required")
            capture_store = RegionalBrowserCaptureStore(
                source_id,
                store=RawDocumentStore(args.raw_root),
            )
            page, total_count, has_next, discovered_ids = (
                capture_store.checkpoint_metadata(capture)
            )
            checkpoint = planned.get(source_id)
            if checkpoint is None:
                checkpoint = checkpoint_store.load(source_id)
                if checkpoint is None:
                    checkpoint = RegionalBatchCheckpoint.initial(source_id)
            if page == checkpoint.next_page:
                next_checkpoint = checkpoint.discover(
                    page=page,
                    external_ids=discovered_ids,
                    total_count=total_count,
                    has_next=has_next,
                )
            elif (
                page < checkpoint.next_page
                and set(discovered_ids).issubset(checkpoint.discovered_ids)
                and (
                    total_count is None
                    or checkpoint.total_count == total_count
                )
            ):
                next_checkpoint = checkpoint
            else:
                raise ValueError(
                    "regional Browser capture does not match checkpoint"
                )
            detail_ids = tuple(
                item["external_id"] for item in capture["items"]
            )
            next_checkpoint = next_checkpoint.capture(detail_ids)
            planned[source_id] = next_checkpoint
            operations.append(
                (capture, capture_store, next_checkpoint, discovered_ids)
            )
    except (OSError, ValueError, json.JSONDecodeError, ExtractionError) as error:
        print(f"regional Browser capture rejected: {error}", file=stderr)
        return 1
    for capture, capture_store, checkpoint, discovered_ids in operations:
        result = None
        try:
            result = capture_store.save(capture)
            checkpoint_store.save(checkpoint)
        except (OSError, ValueError, ExtractionError) as error:
            if result is not None:
                capture_store.remove_result(result)
            print(f"regional Browser capture rejected: {error}", file=stderr)
            return 1
        print(
            "regional Browser capture stored: "
            f"source={result.source_id} page={result.page} "
            f"discovered={len(discovered_ids)} details={result.item_count} "
            f"raw_documents={result.raw_document_count} "
            f"pending_details="
            f"{checkpoint.to_dict()['pending_detail_count']} "
            f"pending_decisions={checkpoint.to_dict()['pending_count']}",
            file=stdout,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
