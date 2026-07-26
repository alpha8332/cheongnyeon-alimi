"""Shared collector infrastructure and registered official sources."""

from collectors.base import (
    CollectionOptions,
    CollectionResult,
    Collector,
    CollectorFactory,
)
from collectors.bokjiro import (
    SOURCE_ID as BOKJIRO_SOURCE_ID,
    create_bokjiro_collector,
)
from collectors.http import HttpClient, HttpClientConfig
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)
from collectors.registry import CollectorRegistry, default_registry
from collectors.storage import RawDocumentStore
from collectors.youthcenter import (
    SOURCE_ID as YOUTHCENTER_SOURCE_ID,
    create_youthcenter_collector,
)


default_registry.register(
    YOUTHCENTER_SOURCE_ID,
    create_youthcenter_collector,
)
default_registry.register(
    BOKJIRO_SOURCE_ID,
    create_bokjiro_collector,
)

__all__ = [
    "CollectionOptions",
    "CollectionResult",
    "Collector",
    "CollectorFactory",
    "CollectorRegistry",
    "HttpClient",
    "HttpClientConfig",
    "RawDocumentRole",
    "RawDocumentStore",
    "RawFormat",
    "RawPolicyDocument",
    "SourceType",
    "default_registry",
]
