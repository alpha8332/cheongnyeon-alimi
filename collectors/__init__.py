"""Shared collector contracts and HTTP infrastructure."""

from collectors.base import Collector, CollectorFactory
from collectors.http import HttpClient, HttpClientConfig
from collectors.registry import CollectorRegistry, default_registry

__all__ = [
    "Collector",
    "CollectorFactory",
    "CollectorRegistry",
    "HttpClient",
    "HttpClientConfig",
    "default_registry",
]
