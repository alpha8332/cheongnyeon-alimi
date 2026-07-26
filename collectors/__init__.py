"""Shared collector contracts and HTTP infrastructure."""

from collectors.base import Collector, CollectorFactory
from collectors.http import HttpClient, HttpClientConfig
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)
from collectors.registry import CollectorRegistry, default_registry
from collectors.storage import RawDocumentStore

__all__ = [
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
