"""Bounded multi-page collection and immutable snapshot manifests."""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from collectors.base import CollectionOptions, Collector


_DOCUMENT_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SnapshotError(RuntimeError):
    """A complete, reproducible source snapshot could not be produced."""


@dataclass(frozen=True, slots=True)
class SnapshotManifest:
    snapshot_id: str
    source_id: str
    started_at: datetime
    completed_at: datetime
    page_size: int
    detail_limit: int
    request_budget: int
    request_count: int
    total_count: int
    item_count: int
    list_response_document_ids: tuple[str, ...]
    detail_document_ids: tuple[str, ...]
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not _DOCUMENT_ID_PATTERN.fullmatch(self.snapshot_id):
            raise SnapshotError("invalid snapshot ID")
        if not _SOURCE_ID_PATTERN.fullmatch(self.source_id):
            raise SnapshotError("invalid snapshot source ID")
        if (
            self.started_at.tzinfo is None
            or self.completed_at.tzinfo is None
            or self.completed_at < self.started_at
        ):
            raise SnapshotError("invalid snapshot timestamps")
        if not 1 <= self.page_size <= 500:
            raise SnapshotError("invalid snapshot page size")
        if not 0 <= self.detail_limit <= 5:
            raise SnapshotError("invalid snapshot detail limit")
        if not 1 <= self.request_count <= self.request_budget <= 100:
            raise SnapshotError("invalid snapshot request counts")
        if self.total_count <= 0 or self.item_count != self.total_count:
            raise SnapshotError("snapshot is not complete")
        if not self.list_response_document_ids:
            raise SnapshotError("snapshot has no list responses")
        document_ids = (
            *self.list_response_document_ids,
            *self.detail_document_ids,
        )
        if any(
            not _DOCUMENT_ID_PATTERN.fullmatch(document_id)
            for document_id in document_ids
        ):
            raise SnapshotError("snapshot contains an invalid document ID")
        if len(set(document_ids)) != len(document_ids):
            raise SnapshotError("snapshot contains duplicate document IDs")
        if self.request_count != len(document_ids):
            raise SnapshotError("snapshot request and Raw counts do not match")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "source_id": self.source_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "page_size": self.page_size,
            "detail_limit": self.detail_limit,
            "request_budget": self.request_budget,
            "request_count": self.request_count,
            "total_count": self.total_count,
            "item_count": self.item_count,
            "list_response_document_ids": list(
                self.list_response_document_ids
            ),
            "detail_document_ids": list(self.detail_document_ids),
        }

    @classmethod
    def from_dict(cls, value: Any) -> SnapshotManifest:
        if not isinstance(value, dict):
            raise SnapshotError("snapshot manifest must be an object")
        expected = {
            "schema_version",
            "snapshot_id",
            "source_id",
            "started_at",
            "completed_at",
            "page_size",
            "detail_limit",
            "request_budget",
            "request_count",
            "total_count",
            "item_count",
            "list_response_document_ids",
            "detail_document_ids",
        }
        if set(value) != expected or value.get("schema_version") != "1.0.0":
            raise SnapshotError("unsupported snapshot manifest")
        try:
            return cls(
                schema_version=value["schema_version"],
                snapshot_id=value["snapshot_id"],
                source_id=value["source_id"],
                started_at=datetime.fromisoformat(value["started_at"]),
                completed_at=datetime.fromisoformat(value["completed_at"]),
                page_size=value["page_size"],
                detail_limit=value["detail_limit"],
                request_budget=value["request_budget"],
                request_count=value["request_count"],
                total_count=value["total_count"],
                item_count=value["item_count"],
                list_response_document_ids=tuple(
                    value["list_response_document_ids"]
                ),
                detail_document_ids=tuple(value["detail_document_ids"]),
            )
        except (KeyError, TypeError, ValueError):
            raise SnapshotError("invalid snapshot manifest") from None


class SnapshotManifestStore:
    def __init__(self, raw_root: str | Path) -> None:
        self.root = Path(raw_root).resolve()
        self.manifest_root = self.root / "_snapshots"

    def save(self, manifest: SnapshotManifest) -> Path:
        target = (
            self.manifest_root
            / manifest.source_id
            / f"{manifest.snapshot_id}.json"
        )
        self._ensure_within_root(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise SnapshotError("snapshot manifest already exists")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".snapshot-",
            suffix=".tmp",
            dir=target.parent,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(
                    manifest.to_dict(),
                    stream,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary_path, target)
        except FileExistsError:
            raise SnapshotError("snapshot manifest already exists") from None
        except OSError:
            raise SnapshotError("snapshot manifest could not be stored") from None
        finally:
            temporary_path.unlink(missing_ok=True)
        return target

    def load(self, source_id: str, snapshot_id: str) -> SnapshotManifest:
        if not _SOURCE_ID_PATTERN.fullmatch(source_id):
            raise SnapshotError("invalid snapshot source ID")
        if not _DOCUMENT_ID_PATTERN.fullmatch(snapshot_id):
            raise SnapshotError("invalid snapshot ID")
        path = self.manifest_root / source_id / f"{snapshot_id}.json"
        self._ensure_within_root(path)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            manifest = SnapshotManifest.from_dict(value)
        except (OSError, json.JSONDecodeError):
            raise SnapshotError("snapshot manifest could not be loaded") from None
        if manifest.source_id != source_id or manifest.snapshot_id != snapshot_id:
            raise SnapshotError("snapshot manifest identity does not match")
        return manifest

    def latest(self, source_id: str) -> SnapshotManifest | None:
        source_root = self.manifest_root / source_id
        self._ensure_within_root(source_root)
        if not source_root.is_dir():
            return None
        manifests = tuple(
            self.load(source_id, path.stem)
            for path in sorted(source_root.glob("*.json"))
        )
        if not manifests:
            return None
        return max(
            manifests,
            key=lambda manifest: (
                manifest.completed_at,
                manifest.snapshot_id,
            ),
        )

    def _ensure_within_root(self, path: Path) -> None:
        try:
            path.resolve().relative_to(self.root)
        except ValueError:
            raise SnapshotError("snapshot path escapes the Raw root") from None


def collect_snapshot(
    collector: Collector,
    *,
    manifest_store: SnapshotManifestStore,
    page_size: int = 500,
    detail_limit: int = 0,
    request_budget: int = 12,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> SnapshotManifest:
    """Collect every reported list item within an explicit request budget."""
    if not 1 <= page_size <= 500:
        raise SnapshotError("page size must be from 1 to 500")
    if not 0 <= detail_limit <= 5:
        raise SnapshotError("detail limit must be from 0 to 5")
    if not 1 <= request_budget <= 100:
        raise SnapshotError("request budget must be from 1 to 100")

    started_at = now()
    page = 1
    request_count = 0
    total_count: int | None = None
    seen_external_ids: set[str] = set()
    response_ids: list[str] = []
    detail_ids: list[str] = []
    remaining_detail = detail_limit

    while True:
        planned_details = remaining_detail if page == 1 else 0
        if request_count + 1 + planned_details > request_budget:
            raise SnapshotError("snapshot request budget is insufficient")
        result = collector.collect(
            CollectionOptions(
                page=page,
                limit=page_size,
                detail_limit=planned_details,
            )
        )
        if (
            result.source_id != collector.source_id
            or result.page != page
            or result.page_size != page_size
            or result.total_count is None
            or result.list_response_document_id is None
        ):
            raise SnapshotError("collector returned incomplete snapshot metadata")
        if (
            result.item_count != len(result.external_ids)
            or result.detail_count != len(result.detail_document_ids)
            or result.detail_count > planned_details
            or result.request_count != 1 + result.detail_count
        ):
            raise SnapshotError("collector snapshot counts do not match")
        if total_count is None:
            total_count = result.total_count
        elif result.total_count != total_count:
            raise SnapshotError("source total count changed during collection")
        duplicate_ids = seen_external_ids.intersection(result.external_ids)
        if duplicate_ids or len(set(result.external_ids)) != len(
            result.external_ids
        ):
            raise SnapshotError("source returned duplicate items across pages")

        seen_external_ids.update(result.external_ids)
        response_ids.append(result.list_response_document_id)
        detail_ids.extend(result.detail_document_ids)
        request_count += result.request_count
        remaining_detail -= result.detail_count

        if request_count > request_budget:
            raise SnapshotError("snapshot request budget was exceeded")
        if len(seen_external_ids) == total_count:
            break
        if len(seen_external_ids) > total_count:
            raise SnapshotError("snapshot item count exceeds source total")
        if result.item_count < page_size:
            raise SnapshotError("source ended before the reported total count")

        required_pages = math.ceil(total_count / page_size)
        remaining_pages = required_pages - page
        if request_count + remaining_pages > request_budget:
            raise SnapshotError("snapshot request budget is insufficient")
        page += 1
        if page > 1000:
            raise SnapshotError("snapshot page limit was exceeded")

    manifest = SnapshotManifest(
        snapshot_id=uuid4().hex,
        source_id=collector.source_id,
        started_at=started_at,
        completed_at=now(),
        page_size=page_size,
        detail_limit=detail_limit,
        request_budget=request_budget,
        request_count=request_count,
        total_count=total_count,
        item_count=len(seen_external_ids),
        list_response_document_ids=tuple(response_ids),
        detail_document_ids=tuple(detail_ids),
    )
    manifest_store.save(manifest)
    return manifest
