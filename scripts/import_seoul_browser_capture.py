"""Persist a validated RYP5 Seoul Browser observation as replayable Raw."""

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
from collectors.regional_pilot import SeoulBrowserCaptureStore  # noqa: E402
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
        if not isinstance(value, dict):
            raise ExtractionError("Browser capture root must be an object")
        result = SeoulBrowserCaptureStore(
            store=RawDocumentStore(args.raw_root)
        ).save(value)
    except (OSError, json.JSONDecodeError, ExtractionError) as error:
        print(f"Seoul Browser capture rejected: {error}", file=stderr)
        return 1
    print(
        "Seoul Browser capture stored: "
        f"items={result.item_count} raw_documents={result.raw_document_count}",
        file=stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
