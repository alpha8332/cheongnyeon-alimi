"""Command-line entry point for registered collectors."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import TextIO

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
        collector = registry.create(source_id)
        collector.collect()
    except CollectorError as error:
        print(f"collector failed: {error}", file=stderr)
        return 1
    except Exception:
        print(
            f"collector failed unexpectedly: source={source_id}",
            file=stderr,
        )
        return 1

    print(f"collector completed: source={source_id}", file=stdout)
    return 0
