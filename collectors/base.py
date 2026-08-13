"""Common contracts implemented by source collectors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TypeAlias

from collectors.errors import CollectorConfigurationError


@dataclass(frozen=True, slots=True)
class CollectionOptions:
    page: int = 1
    limit: int = 10
    detail_limit: int = 3
    detail_offset: int = 0

    def __post_init__(self) -> None:
        if (
            not isinstance(self.page, int)
            or isinstance(self.page, bool)
            or not 1 <= self.page <= 1000
        ):
            raise CollectorConfigurationError(
                "page must be an integer from 1 to 1000"
            )
        if (
            not isinstance(self.limit, int)
            or isinstance(self.limit, bool)
            or not 1 <= self.limit <= 500
        ):
            raise CollectorConfigurationError(
                "limit must be an integer from 1 to 500"
            )
        if (
            not isinstance(self.detail_limit, int)
            or isinstance(self.detail_limit, bool)
            or not 0 <= self.detail_limit <= 5
        ):
            raise CollectorConfigurationError(
                "detail_limit must be an integer from 0 to 5"
            )
        if (
            not isinstance(self.detail_offset, int)
            or isinstance(self.detail_offset, bool)
            or not 0 <= self.detail_offset <= 500
        ):
            raise CollectorConfigurationError(
                "detail_offset must be an integer from 0 to 500"
            )


@dataclass(frozen=True, slots=True)
class CollectionResult:
    source_id: str
    request_count: int
    item_count: int
    detail_count: int
    stored_paths: tuple[Path, ...]
    page: int | None = None
    page_size: int | None = None
    total_count: int | None = None
    external_ids: tuple[str, ...] = ()
    list_response_document_id: str | None = None
    detail_document_ids: tuple[str, ...] = ()

    @property
    def raw_document_count(self) -> int:
        return len(self.stored_paths)


class Collector(Protocol):
    """Minimum contract required by the registry and command-line runner."""

    source_id: str

    def collect(
        self,
        options: CollectionOptions | None = None,
    ) -> CollectionResult:
        """Collect source data without printing response payloads."""


CollectorFactory: TypeAlias = Callable[[], Collector]
