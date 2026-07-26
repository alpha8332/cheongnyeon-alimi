"""Collector factory registry."""

from __future__ import annotations

import re

from collectors.base import Collector, CollectorFactory
from collectors.errors import CollectorConfigurationError


SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CollectorRegistry:
    """Map stable source IDs to zero-argument collector factories."""

    def __init__(self) -> None:
        self._factories: dict[str, CollectorFactory] = {}

    def register(self, source_id: str, factory: CollectorFactory) -> None:
        if not SOURCE_ID_PATTERN.fullmatch(source_id):
            raise CollectorConfigurationError(
                f"invalid source ID: {source_id!r}"
            )
        if source_id in self._factories:
            raise CollectorConfigurationError(
                f"collector is already registered: {source_id}"
            )
        self._factories[source_id] = factory

    def create(self, source_id: str) -> Collector:
        try:
            factory = self._factories[source_id]
        except KeyError as error:
            raise CollectorConfigurationError(
                f"unknown source ID: {source_id}"
            ) from error

        collector = factory()
        if collector.source_id != source_id:
            raise CollectorConfigurationError(
                "collector source ID does not match its registry entry"
            )
        return collector

    def source_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))


default_registry = CollectorRegistry()
