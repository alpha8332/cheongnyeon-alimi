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
from collectors.cross_source_duplicate import (
    AGGREGATOR_SOURCE_IDS,
    AggregatorBaseline,
    AnnouncementIdentity,
    BaselineDescriptor,
    BaselineRecord,
    CrossSourceDecisionManifest,
    CrossSourceDecisionManifestStore,
    DuplicateDecision,
    DuplicateEvidence,
    DuplicateOutcome,
    PolicyIdentity,
    evaluate_cross_source_duplicate,
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
    map_eligibility,
    map_bokjiro_eligibility,
    map_cheonan_eligibility,
    map_youthcenter_eligibility,
)
from collectors.http import HttpClient, HttpClientConfig
from collectors.gyeongbuk_youth import (
    SOURCE_ID as GYEONGBUK_YOUTH_SOURCE_ID,
    GyeongbukYouthExtractor,
    create_gyeongbuk_youth_collector,
    decide_gyeongbuk_regional_policy,
    map_gyeongbuk_duplicate_evidence,
)
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
from collectors.regional_sources import (
    RegionalSourceInventoryValidator,
    regional_source_inventory_issues,
)
from collectors.regional_profile import (
    RegionalSourceProfile,
    load_approved_regional_profile,
    replay_profile_actions,
)
from collectors.regional_policy_gate import (
    ApplicationAvailability,
    RegionalityStatus,
    RegionalPolicyDecision,
    RegionalPolicyEvidence,
    evaluate_regional_policy,
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
default_registry.register(
    GYEONGBUK_YOUTH_SOURCE_ID,
    create_gyeongbuk_youth_collector,
)

__all__ = [
    "AGGREGATOR_SOURCE_IDS",
    "AggregatorBaseline",
    "AnnouncementIdentity",
    "ApplicationSchedule",
    "ApplicationStatus",
    "ApplicationAvailability",
    "BaselineDescriptor",
    "BaselineRecord",
    "Category",
    "CollectionOptions",
    "CollectionResult",
    "Collector",
    "CollectorFactory",
    "CollectorRegistry",
    "CrossSourceDecisionManifest",
    "CrossSourceDecisionManifestStore",
    "CoverageScope",
    "CheonanYouthCenterExtractor",
    "DataQualityStatus",
    "DuplicateDecision",
    "DuplicateEvidence",
    "DuplicateOutcome",
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
    "GyeongbukYouthExtractor",
    "InstitutionalContact",
    "InstitutionalContactKind",
    "JsonSchemaValidator",
    "NormalizedProgram",
    "NormalizedProgramValidator",
    "Normalizer",
    "PolicyIdentity",
    "BokjiroExtractor",
    "RawDocumentRole",
    "RawDocumentStore",
    "RawFormat",
    "RawPolicyDocument",
    "RegionRelation",
    "RegionResolutionStatus",
    "RegionRule",
    "RegionalSourceInventoryValidator",
    "RegionalityStatus",
    "RegionalPolicyDecision",
    "RegionalPolicyEvidence",
    "RegionalSourceProfile",
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
    "map_eligibility",
    "map_youthcenter_eligibility",
    "regional_source_inventory_issues",
    "decide_gyeongbuk_regional_policy",
    "evaluate_cross_source_duplicate",
    "evaluate_regional_policy",
    "load_approved_regional_profile",
    "map_gyeongbuk_duplicate_evidence",
    "replay_profile_actions",
]
