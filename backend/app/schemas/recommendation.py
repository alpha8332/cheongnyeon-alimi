from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


RecommendationStatus = Literal["open", "upcoming", "closed"]


class RecommendationRequest(BaseModel):
    """맞춤 정책 추천 요청 DTO."""
    age: Optional[int] = Field(default=None, ge=0, le=120, description="사용자 만 연령")
    region: Optional[str] = Field(default=None, description="거주지 (예: 서울특별시, 경기도)")
    category: Optional[str] = Field(default=None, description="관심 정책 분야 (예: finance, housing, employment, education)")
    categories: List[str] = Field(
        default_factory=list,
        max_length=7,
        description="복수 관심 정책 분야. 하나 이상 부합하면 추천 후보로 평가",
    )
    status: Optional[RecommendationStatus] = Field(
        default=None,
        description="신청 상태 필터 (open, upcoming, closed)",
    )
    include_partial: bool = Field(default=False, description="품질 상태가 partial인 정책 포함 여부")
    limit: int = Field(default=10, ge=1, le=50, description="최대 추천 반환 수")


class RecommendationReason(BaseModel):
    """추천 사유 항목 DTO."""
    code: str = Field(description="추천 사유 코드 (MATCHED_CATEGORY, MATCHED_REGION, MATCHED_AGE, MATCHED_STATUS 등)")
    label: str = Field(description="사람이 읽을 수 있는 추천 사유 설명 문구")


class RecommendationItem(BaseModel):
    """추천 정책 아이템 DTO."""
    id: int
    source_id: str
    external_id: str
    title: str
    lead: Optional[str] = None
    category: str
    regions: List[str] = Field(default_factory=list)
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    application_start: Optional[str] = None
    application_end: Optional[str] = None
    application_status: str
    data_quality_status: str = "valid"
    score: int = Field(description="추천 부합도 점수")
    reasons: List[RecommendationReason] = Field(default_factory=list, description="추천 사유 목록")
    unknown_conditions: List[str] = Field(default_factory=list, description="데이터로 확인할 수 없는 미확정 조건")
    disclaimer: str = Field(
        default="본 추천 결과는 자격을 확정하지 않으며, 상세 자격 및 신청 조건은 공식 원문에서 확인해야 합니다.",
        description="비단정 안내 문구"
    )

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    """맞춤 정책 추천 응답 DTO."""
    items: List[RecommendationItem]
    total: int
    evaluated_at: str = Field(description="추천 평가 수행 ISO-8601 시각")
