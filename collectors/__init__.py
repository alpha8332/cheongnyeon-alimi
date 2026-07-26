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
from collectors.extracted import ExtractedPolicy, SourceProvenance
from collectors.extractors import BokjiroExtractor, YouthCenterExtractor
from collectors.http import HttpClient, HttpClientConfig
from collectors.normalized import (
    ApplicationSchedule,
    ApplicationStatus,
    Category,
    DataQualityStatus,
    NormalizedProgram,
)
from collectors.normalizer import Normalizer
from collectors.profile import FieldStatistics, SourceFieldProfile
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)
from collectors.registry import CollectorRegistry, default_registry
from collectors.storage import RawDocumentStore
from collectors.validation import (
    NormalizedProgramValidator,
    ValidationIssue,
    ValidationPartition,
    ValidationResult,
)
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
    "ApplicationSchedule",
    "ApplicationStatus",
    "Category",
    "CollectionOptions",
    "CollectionResult",
    "Collector",
    "CollectorFactory",
    "CollectorRegistry",
    "DataQualityStatus",
    "ExtractedPolicy",
    "FieldStatistics",
    "HttpClient",
    "HttpClientConfig",
    "NormalizedProgram",
    "NormalizedProgramValidator",
    "Normalizer",
    "BokjiroExtractor",
    "RawDocumentRole",
    "RawDocumentStore",
    "RawFormat",
    "RawPolicyDocument",
    "SourceType",
    "SourceFieldProfile",
    "SourceProvenance",
    "ValidationIssue",
    "ValidationPartition",
    "ValidationResult",
    "YouthCenterExtractor",
    "default_registry",
]
