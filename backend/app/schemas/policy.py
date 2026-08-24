from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


PolicyCategory = Literal[
    "housing",
    "finance",
    "welfare",
    "employment",
    "startup",
    "education",
    "other",
]
ApplicationSchedule = Literal[
    "fixed_period",
    "always",
    "until_budget_exhausted",
]
ApplicationStatus = Literal["open", "closed", "scheduled"]
DataQualityStatus = Literal["valid", "partial"]
EligibilityCoverage = Literal["complete", "partial", "unknown"]
EligibilityCategory = Literal[
    "age",
    "region",
    "income",
    "asset",
    "employment",
    "education",
    "housing",
    "household",
    "other",
]
EvidenceLocatorType = Literal["source_field", "css_selector"]
InstitutionalContactKind = Literal["phone", "official_channel"]


class EligibilityEvidenceRead(BaseModel):
    source_id: str
    source_url: str
    collected_at: datetime
    locator_type: EvidenceLocatorType
    locator: str


class EligibilityConditionRead(BaseModel):
    category: EligibilityCategory
    text: str
    evidence: list[EligibilityEvidenceRead]


class EligibilityDocumentRead(BaseModel):
    text: str
    evidence: list[EligibilityEvidenceRead]


class InstitutionalContactRead(BaseModel):
    kind: InstitutionalContactKind
    label: str
    value: str
    evidence: list[EligibilityEvidenceRead]


class EligibilitySummaryRead(BaseModel):
    coverage: EligibilityCoverage
    requirements: list[EligibilityConditionRead]
    exclusions: list[EligibilityConditionRead]
    preferences: list[EligibilityConditionRead]
    documents: list[EligibilityDocumentRead]
    unknowns: list[EligibilityConditionRead]
    institutional_contacts: list[InstitutionalContactRead]


class PolicyBase(BaseModel):
    schema_version: str = "1.0.0"
    source_id: str
    source_name: str
    external_id: str | None = None
    title: str
    organization: str | None = None
    summary: str | None = None
    category_text: str | None = None
    categories: list[PolicyCategory]
    application_period_text: str | None = None
    application_start: date | None = None
    application_end: date | None = None
    application_schedule: ApplicationSchedule | None = None
    application_status: ApplicationStatus | None = None
    region_text: str | None = None
    regions: list[str]
    age_min: int | None = None
    age_max: int | None = None
    age_condition_text: str | None = None
    eligibility_text: str | None = None
    support_content: str | None = None
    application_method: str | None = None
    education_statuses: list[str]
    employment_statuses: list[str]
    required_conditions: list[str]
    preferred_conditions: list[str]
    excluded_conditions: list[str]
    source_url: str
    collected_at: datetime
    data_quality_status: DataQualityStatus


class PolicyRead(PolicyBase):
    """Public policy response. Raw provenance is intentionally excluded."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PolicyDetailRead(PolicyRead):
    """Detail response with source-backed eligibility evidence."""

    eligibility_summary: EligibilitySummaryRead


class PolicyListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[PolicyRead]
