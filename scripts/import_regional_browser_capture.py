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
from collectors.regional_expansion import RegionalBrowserCaptureStore  # noqa: E402
from collectors.storage import RawDocumentStore  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("--raw-root", type=Path, default=Path("runtime/raw"))
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
        results = []
        for capture in captures:
            source_id = capture.get("source_id")
            if not isinstance(source_id, str):
                raise ExtractionError("Browser capture source_id is required")
            results.append(
                RegionalBrowserCaptureStore(
                    source_id,
                    store=RawDocumentStore(args.raw_root),
                ).save(capture)
            )
    except (OSError, ValueError, json.JSONDecodeError, ExtractionError) as error:
        print(f"regional Browser capture rejected: {error}", file=stderr)
        return 1
    for result in results:
        print(
            "regional Browser capture stored: "
            f"source={result.source_id} page={result.page} "
            f"items={result.item_count} raw_documents={result.raw_document_count}",
            file=stdout,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
