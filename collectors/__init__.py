"""Shared collector infrastructure and registered official sources."""

from functools import partial

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
    map_regional_eligibility,
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
from collectors.regional_pilot import (
    BUSAN_SOURCE_ID,
    SEOUL_SOURCE_ID,
    BusanYouthExtractor,
    SeoulBrowserCaptureStore,
    SeoulYouthExtractor,
    create_busan_youth_collector,
    decide_representative_regional_policy,
    map_representative_duplicate_evidence,
)
from collectors.regional_expansion import (
    EXPANDED_CAPTURE_SOURCE_IDS,
    REGIONAL_EXPANSION_SPECS,
    RegionalBatchCheckpoint,
    RegionalBrowserCaptureStore,
    RegionalBrowserExtractor,
    RegionalCheckpointStore,
    RegionalOutcome,
    decide_expanded_regional_policy,
    map_expanded_duplicate_evidence,
    outcome_from_decisions,
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
    RegionalSourceScopeEvidence,
    enforce_youth_target,
    evaluate_regional_policy,
)
from collectors.registry import CollectorRegistry, default_registry
from collectors.storage import RawDocumentStore
from collectors.supplemental_official import (
    KINFA_SOURCE_ID,
    KPASS_SOURCE_ID,
    KOSAF_SOURCE_ID,
    LH_SOURCE_ID,
    SUPPLEMENTAL_SOURCE_IDS,
    WORK24_SOURCE_ID,
    SupplementalDecision,
    SupplementalListItem,
    SupplementalOfficialCollector,
    SupplementalOfficialExtractor,
    SupplementalOutcome,
    create_supplemental_official_collector,
    decide_supplemental_policy,
    discover_supplemental_list_items,
    map_supplemental_duplicate_evidence,
    supplemental_http_config_from_environment,
)
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
default_registry.register(
    BUSAN_SOURCE_ID,
    create_busan_youth_collector,
)
for _supplemental_source_id in sorted(SUPPLEMENTAL_SOURCE_IDS):
    default_registry.register(
        _supplemental_source_id,
        partial(
            create_supplemental_official_collector,
            _supplemental_source_id,
        ),
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
    "BUSAN_SOURCE_ID",
    "Category",
    "CollectionOptions",
    "CollectionResult",
    "Collector",
    "CollectorFactory",
    "CollectorRegistry",
    "CrossSourceDecisionManifest",
    "CrossSourceDecisionManifestStore",
    "EXPANDED_CAPTURE_SOURCE_IDS",
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
    "BusanYouthExtractor",
    "InstitutionalContact",
    "InstitutionalContactKind",
    "KINFA_SOURCE_ID",
    "KPASS_SOURCE_ID",
    "KOSAF_SOURCE_ID",
    "JsonSchemaValidator",
    "LH_SOURCE_ID",
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
    "REGIONAL_EXPANSION_SPECS",
    "RegionalBatchCheckpoint",
    "RegionalBrowserCaptureStore",
    "RegionalBrowserExtractor",
    "RegionalCheckpointStore",
    "RegionalOutcome",
    "RegionalSourceInventoryValidator",
    "RegionalityStatus",
    "RegionalPolicyDecision",
    "RegionalPolicyEvidence",
    "RegionalSourceScopeEvidence",
    "RegionalSourceProfile",
    "SEOUL_SOURCE_ID",
    "SeoulBrowserCaptureStore",
    "SeoulYouthExtractor",
    "RequiredDocument",
    "SourceType",
    "SourceFieldProfile",
    "SourceProvenance",
    "SUPPLEMENTAL_SOURCE_IDS",
    "SupplementalDecision",
    "SupplementalListItem",
    "SupplementalOfficialCollector",
    "SupplementalOfficialExtractor",
    "SupplementalOutcome",
    "ValidationIssue",
    "ValidationPartition",
    "ValidationResult",
    "YouthCenterExtractor",
    "WORK24_SOURCE_ID",
    "default_registry",
    "map_bokjiro_eligibility",
    "map_cheonan_eligibility",
    "map_regional_eligibility",
    "map_eligibility",
    "map_youthcenter_eligibility",
    "regional_source_inventory_issues",
    "decide_gyeongbuk_regional_policy",
    "decide_supplemental_policy",
    "create_supplemental_official_collector",
    "decide_expanded_regional_policy",
    "decide_representative_regional_policy",
    "evaluate_cross_source_duplicate",
    "enforce_youth_target",
    "evaluate_regional_policy",
    "discover_supplemental_list_items",
    "load_approved_regional_profile",
    "map_gyeongbuk_duplicate_evidence",
    "map_expanded_duplicate_evidence",
    "map_representative_duplicate_evidence",
    "map_supplemental_duplicate_evidence",
    "supplemental_http_config_from_environment",
    "outcome_from_decisions",
    "replay_profile_actions",
]
