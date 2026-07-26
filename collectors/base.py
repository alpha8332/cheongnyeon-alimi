"""Common contracts implemented by source collectors."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, TypeAlias


class Collector(Protocol):
    """Minimum contract required by the registry and command-line runner."""

    source_id: str

    def collect(self) -> object:
        """Collect source data without printing response payloads."""


CollectorFactory: TypeAlias = Callable[[], Collector]
