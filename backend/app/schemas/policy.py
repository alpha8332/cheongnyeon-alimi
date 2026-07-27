from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field

class PolicyBase(BaseModel):
    schema_version: str = "1.0.0"
    source_id: str
    source_name: str
    external_id: Optional[str] = None
    title: str
    organization: Optional[str] = None
    summary: Optional[str] = None
    category_text: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    application_period_text: Optional[str] = None
    application_start: Optional[date] = None
    application_end: Optional[date] = None
    application_schedule: Optional[str] = None
    application_status: Optional[str] = None
    region_text: Optional[str] = None
    regions: List[str] = Field(default_factory=list)
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
    collected_at: datetime
    data_quality_status: str

class PolicyRead(PolicyBase):
    """
    일반 사용자 정책 Response Schema (4-A: provenance 비노출)
    """
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PolicyListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[PolicyRead]
