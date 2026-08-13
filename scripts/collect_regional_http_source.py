"""Fully capture one approved RYP6 HTTP Source with resumable checkpoints."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.base import CollectionOptions  # noqa: E402
from collectors.gyeongbuk_youth import (  # noqa: E402
    SOURCE_ID as GYEONGBUK_SOURCE_ID,
    GyeongbukYouthCollector,
)
from collectors.raw import RawDocumentRole  # noqa: E402
from collectors.regional_expansion import (  # noqa: E402
    REGIONAL_PAGINATION_SPECS,
    RegionalBatchCheckpoint,
    RegionalCheckpointStore,
)
from collectors.regional_pilot import (  # noqa: E402
    BUSAN_SOURCE_ID,
    BusanYouthCollector,
)
from collectors.storage import RawDocumentStore  # noqa: E402


HTTP_SOURCE_IDS = (BUSAN_SOURCE_ID, GYEONGBUK_SOURCE_ID)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=HTTP_SOURCE_IDS, required=True)
    parser.add_argument("--raw-root", type=Path, default=Path("runtime/raw"))
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=Path("runtime/decisions/regional-checkpoints"),
    )
    parser.add_argument("--detail-batch", type=int, default=3)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 1 <= args.detail_batch <= 3:
        print("regional HTTP capture rejected: detail batch must be 1 to 3")
        return 1

    raw_store = RawDocumentStore(args.raw_root)
    checkpoint_store = RegionalCheckpointStore(args.checkpoint_root)
    checkpoint = checkpoint_store.load(args.source)
    if checkpoint is None:
        checkpoint = RegionalBatchCheckpoint.initial(args.source)
    collector = (
        BusanYouthCollector(store=raw_store)
        if args.source == BUSAN_SOURCE_ID
        else GyeongbukYouthCollector(store=raw_store)
    )
    pagination = REGIONAL_PAGINATION_SPECS[args.source]
    seen: list[str] = []
    seen_set: set[str] = set()
    total_count: int | None = None

    try:
        for page in range(1, pagination.safety_max_pages + 1):
            discovery = collector.collect(
                CollectionOptions(page=page, limit=500, detail_limit=0)
            )
            page_ids = tuple(discovery.external_ids)
            if (
                not page_ids
                or len(page_ids) != len(set(page_ids))
                or seen_set.intersection(page_ids)
                or discovery.total_count is None
            ):
                raise RuntimeError("HTTP Source returned invalid page identities")
            if total_count is None:
                total_count = discovery.total_count
            elif total_count != discovery.total_count:
                raise RuntimeError("HTTP Source total drifted during traversal")
            seen.extend(page_ids)
            seen_set.update(page_ids)
            if len(seen) > total_count:
                raise RuntimeError("HTTP Source exceeded its reported total")
            has_next = len(seen) < total_count
            pagination.validate_page(
                page=page,
                discovered_count=len(page_ids),
                total_count=total_count,
                has_next=has_next,
            )

            start = len(seen) - len(page_ids)
            known_page_ids = checkpoint.discovered_ids[
                start : start + len(page_ids)
            ]
            if page < checkpoint.next_page:
                if known_page_ids != page_ids:
                    raise RuntimeError(
                        "HTTP Source changed before checkpoint resume"
                    )
            elif page == checkpoint.next_page:
                checkpoint = checkpoint.discover(
                    page=page,
                    external_ids=page_ids,
                    total_count=total_count,
                    has_next=has_next,
                )
                checkpoint_store.save(checkpoint)
            else:
                raise RuntimeError("HTTP checkpoint skipped a page")

            captured = set(checkpoint.captured_ids)
            index = 0
            while index < len(page_ids):
                if page_ids[index] in captured:
                    index += 1
                    continue
                batch_start = index
                batch: list[str] = []
                while (
                    index < len(page_ids)
                    and page_ids[index] not in captured
                    and len(batch) < args.detail_batch
                ):
                    batch.append(page_ids[index])
                    index += 1
                result = collector.collect(
                    CollectionOptions(
                        page=page,
                        limit=500,
                        detail_limit=len(batch),
                        detail_offset=batch_start,
                    )
                )
                stored_documents = tuple(
                    raw_store.load(path) for path in result.stored_paths
                )
                detail_ids = tuple(
                    document.external_id
                    for document in stored_documents
                    if document.document_role
                    is RawDocumentRole.DETAIL_RESPONSE
                )
                if detail_ids != tuple(batch):
                    _rollback(result.stored_paths, raw_store.root)
                    raise RuntimeError("HTTP detail batch identity drifted")
                try:
                    next_checkpoint = checkpoint.capture(batch)
                    checkpoint_store.save(next_checkpoint)
                except Exception:
                    _rollback(result.stored_paths, raw_store.root)
                    raise
                checkpoint = next_checkpoint
                captured.update(batch)
                print(
                    "regional HTTP detail stored: "
                    f"source={args.source} page={page} "
                    f"captured={len(checkpoint.captured_ids)}/"
                    f"{checkpoint.total_count}"
                )

            print(
                "regional HTTP page reconciled: "
                f"source={args.source} page={page} "
                f"discovered={len(seen)}/{total_count}"
            )
            if not has_next:
                break
        else:
            raise RuntimeError("HTTP Source reached the pagination safety limit")

        if (
            not checkpoint.discovery_complete
            or checkpoint.total_count != len(checkpoint.discovered_ids)
            or checkpoint.discovered_ids != checkpoint.captured_ids
        ):
            raise RuntimeError("HTTP Source checkpoint is incomplete")
    except Exception as error:
        print(f"regional HTTP capture failed: {error}", file=sys.stderr)
        return 1

    print(
        "regional HTTP capture completed: "
        f"source={args.source} total={checkpoint.total_count} "
        f"pending_decisions={checkpoint.to_dict()['pending_count']}"
    )
    return 0


def _rollback(paths: tuple[Path, ...], root: Path) -> None:
    for path in reversed(paths):
        path.unlink(missing_ok=True)
        parent = path.parent
        while parent != root:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent


if __name__ == "__main__":
    raise SystemExit(main())
