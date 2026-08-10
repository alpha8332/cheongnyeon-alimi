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
from collectors.cheonan_youthcenter import (
    SOURCE_ID as CHEONAN_YOUTHCENTER_SOURCE_ID,
    CheonanYouthCenterExtractor,
    create_cheonan_youthcenter_collector,
)
from collectors.extracted import ExtractedPolicy, SourceProvenance
from collectors.extractors import BokjiroExtractor, YouthCenterExtractor
from collectors.eligibility import (
    EligibilityCategory,
    EligibilityContractError,
    EligibilityCoverage,
    EligibilityEvidenceItem,
    EligibilitySummary,
    EvidenceLocatorType,
    EvidenceReference,
    InstitutionalContact,
    InstitutionalContactKind,
    RequiredDocument,
)
from collectors.eligibility_mapping import (
    map_bokjiro_eligibility,
    map_cheonan_eligibility,
    map_youthcenter_eligibility,
)
from collectors.http import HttpClient, HttpClientConfig
from collectors.normalized import (
    ApplicationSchedule,
    ApplicationStatus,
    Category,
    CoverageScope,
    DataQualityStatus,
    NormalizedProgram,
    RegionRelation,
    RegionResolutionStatus,
    RegionRule,
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
    JsonSchemaValidator,
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
default_registry.register(
    CHEONAN_YOUTHCENTER_SOURCE_ID,
    create_cheonan_youthcenter_collector,
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
    "CoverageScope",
    "CheonanYouthCenterExtractor",
    "DataQualityStatus",
    "EligibilityCategory",
    "EligibilityContractError",
    "EligibilityCoverage",
    "EligibilityEvidenceItem",
    "EligibilitySummary",
    "EvidenceLocatorType",
    "EvidenceReference",
    "ExtractedPolicy",
    "FieldStatistics",
    "HttpClient",
    "HttpClientConfig",
    "InstitutionalContact",
    "InstitutionalContactKind",
    "JsonSchemaValidator",
    "NormalizedProgram",
    "NormalizedProgramValidator",
    "Normalizer",
    "BokjiroExtractor",
    "RawDocumentRole",
    "RawDocumentStore",
    "RawFormat",
    "RawPolicyDocument",
    "RegionRelation",
    "RegionResolutionStatus",
    "RegionRule",
    "RequiredDocument",
    "SourceType",
    "SourceFieldProfile",
    "SourceProvenance",
    "ValidationIssue",
    "ValidationPartition",
    "ValidationResult",
    "YouthCenterExtractor",
    "default_registry",
    "map_bokjiro_eligibility",
    "map_cheonan_eligibility",
    "map_youthcenter_eligibility",
]
