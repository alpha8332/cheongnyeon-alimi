"""Collect one complete, bounded release snapshot from an official source."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.bokjiro import (  # noqa: E402
    SOURCE_ID as BOKJIRO_SOURCE_ID,
    BokjiroCollector,
)
from collectors.config import (  # noqa: E402
    http_config_from_environment,
    required_secret,
)
from collectors.errors import CollectorError  # noqa: E402
from collectors.http import HttpClient  # noqa: E402
from collectors.snapshot import (  # noqa: E402
    SnapshotError,
    SnapshotManifestStore,
    collect_snapshot,
)
from collectors.storage import RawDocumentStore  # noqa: E402
from collectors.supplemental_official import (  # noqa: E402
    SUPPLEMENTAL_SOURCE_IDS,
    SupplementalOfficialCollector,
    supplemental_http_config_from_environment,
)
from collectors.youthcenter import (  # noqa: E402
    SOURCE_ID as YOUTHCENTER_SOURCE_ID,
    YouthCenterCollector,
)


SOURCE_IDS = (
    BOKJIRO_SOURCE_ID,
    YOUTHCENTER_SOURCE_ID,
    *tuple(sorted(SUPPLEMENTAL_SOURCE_IDS)),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect a complete source list within a request budget."
    )
    parser.add_argument("--source", required=True, choices=SOURCE_IDS)
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("runtime/raw"),
    )
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--detail-limit", type=int, default=0)
    parser.add_argument("--request-budget", type=int, default=12)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    args = build_parser().parse_args(argv)
    if args.source == YOUTHCENTER_SOURCE_ID and args.detail_limit:
        print(
            "snapshot collection failed: youthcenter detail limit must be 0",
            file=stderr,
        )
        return 2

    try:
        store = RawDocumentStore(args.raw_root)
        http_config = (
            supplemental_http_config_from_environment()
            if args.source in SUPPLEMENTAL_SOURCE_IDS
            else http_config_from_environment()
        )
        http_client = HttpClient(config=http_config)
        if args.source == YOUTHCENTER_SOURCE_ID:
            collector = YouthCenterCollector(
                api_key=required_secret("YOUTHCENTER_API_KEY"),
                http_client=http_client,
                store=store,
            )
        elif args.source == BOKJIRO_SOURCE_ID:
            collector = BokjiroCollector(
                api_key=required_secret("BOKJIRO_API_KEY"),
                http_client=http_client,
                store=store,
            )
        else:
            collector = SupplementalOfficialCollector(
                args.source,
                http_client=http_client,
                store=store,
            )
        manifest = collect_snapshot(
            collector,
            manifest_store=SnapshotManifestStore(args.raw_root),
            page_size=args.page_size,
            detail_limit=args.detail_limit,
            request_budget=args.request_budget,
        )
    except (CollectorError, SnapshotError) as exc:
        print(f"snapshot collection failed: {exc}", file=stderr)
        return 1
    except Exception as exc:
        print(
            "snapshot collection failed unexpectedly: "
            f"source={args.source} error_type={type(exc).__name__}",
            file=stderr,
        )
        return 1

    print(
        "snapshot collection completed: "
        f"source={manifest.source_id} "
        f"requests={manifest.request_count} "
        f"items={manifest.item_count} "
        f"details={len(manifest.detail_document_ids)} "
        f"pages={len(manifest.list_response_document_ids)} "
        f"snapshot_id={manifest.snapshot_id}",
        file=stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
