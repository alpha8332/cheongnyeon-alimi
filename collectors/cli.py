"""Command-line entry point for registered collectors."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import TextIO

from collectors.base import CollectionOptions, CollectionResult
from collectors.errors import CollectorError
from collectors.registry import CollectorRegistry, default_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m collectors")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--source",
        metavar="SOURCE_ID",
        help="run the collector registered for SOURCE_ID",
    )
    selection.add_argument(
        "--list-sources",
        action="store_true",
        help="list registered source IDs",
    )
    parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="source page number (default: 1)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="maximum list items requested (default: 10)",
    )
    parser.add_argument(
        "--detail-limit",
        type=int,
        default=3,
        help="maximum detail requests, from 0 to 5 (default: 3)",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    registry: CollectorRegistry = default_registry,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    args = build_parser().parse_args(argv)
    if args.list_sources:
        for source_id in registry.source_ids():
            print(source_id, file=stdout)
        return 0

    source_id = args.source
    try:
        options = CollectionOptions(
            page=args.page,
            limit=args.limit,
            detail_limit=args.detail_limit,
        )
        collector = registry.create(source_id)
        result = collector.collect(options)
    except CollectorError as error:
        print(f"collector failed: {error}", file=stderr)
        return 1
    except Exception:
        print(
            f"collector failed unexpectedly: source={source_id}",
            file=stderr,
        )
        return 1

    if isinstance(result, CollectionResult):
        print(
            "collector completed: "
            f"source={source_id} "
            f"requests={result.request_count} "
            f"items={result.item_count} "
            f"details={result.detail_count} "
            f"raw_documents={result.raw_document_count}",
            file=stdout,
        )
    else:
        print(f"collector completed: source={source_id}", file=stdout)
    return 0
