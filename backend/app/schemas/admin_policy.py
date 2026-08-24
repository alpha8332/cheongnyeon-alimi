from datetime import date, datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.policy import ApplicationStatus, DataQualityStatus, PolicyCategory


AdminPolicySortBy = Literal["id", "created_at", "updated_at", "title", "collected_at"]
SortOrder = Literal["asc", "desc"]


class AdminPolicyItem(BaseModel):
    """관리자 정책 데이터 표 Row DTO."""
    id: int
    source_id: str
    source_name: str
    external_id: Optional[str] = None
    title: str
    organization: Optional[str] = None
    categories: List[PolicyCategory] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list)
    data_quality_status: DataQualityStatus
    application_status: Optional[ApplicationStatus] = None
    application_start: Optional[date] = None
    application_end: Optional[date] = None
    collected_at: datetime
    last_seen_at: datetime
    last_verified_at: datetime
    inactive_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminPolicyDetail(AdminPolicyItem):
    """관리자 정책 데이터 단건 상세 DTO."""
    summary: Optional[str] = None
    category_text: Optional[str] = None
    region_text: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    age_condition_text: Optional[str] = None
    eligibility_text: Optional[str] = None
    support_content: Optional[str] = None
    application_method: Optional[str] = None
    education_statuses: List[str] = Field(default_factory=list)
    employment_statuses: List[str] = Field(default_factory=list)
    required_conditions: List[str] = Field(default_factory=list)
    preferred_conditions: List[str] = Field(default_factory=list)
    excluded_conditions: List[str] = Field(default_factory=list)
    source_url: str


class AdminPolicyListResponse(BaseModel):
    """관리자 정책 데이터 표 목록 응답 DTO."""
    total: int
    page: int
    limit: int
    items: List[AdminPolicyItem]
