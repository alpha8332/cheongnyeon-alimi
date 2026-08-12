from datetime import date, datetime
from typing import Literal, Optional

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


class ItemEvidence(BaseModel):
    """출처 보증(Evidence) 메타데이터 DTO."""
    source_id: str
    source_url: str
    collected_at: str


class ItemCondition(BaseModel):
    """구조화 조건 항목 DTO (필수/제외/우대)."""
    category: str = "other"  # age, region, income, asset, employment, education, housing, household, other
    content: str
    evidence: Optional[ItemEvidence] = None


class ItemDocument(BaseModel):
    """제출 서류 항목 DTO."""
    name: str
    content: Optional[str] = None
    evidence: Optional[ItemEvidence] = None


class InstitutionalContact(BaseModel):
    """공개 시설/기관 공식 문의처 DTO."""
    label: str
    value: str
    contact_type: str = "phone"  # phone, url, email


class EligibilitySummaryResponse(BaseModel):
    """핵심 신청 조건 요약 & Evidence 구조체 DTO."""
    status: Literal["complete", "partial", "unknown"] = "partial"
    requirements: list[ItemCondition] = []
    exclusions: list[ItemCondition] = []
    preferences: list[ItemCondition] = []
    required_documents: list[ItemDocument] = []
    unknown_conditions: list[str] = []
    institutional_contacts: list[InstitutionalContact] = []


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
    eligibility_summary: Optional[EligibilitySummaryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PolicyListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[PolicyRead]
