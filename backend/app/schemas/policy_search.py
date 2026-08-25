from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.policy import (
    ApplicationStatus,
    PolicyCategory,
    PolicyRead,
    PolicySort,
)

SearchDimension = Literal["keyword", "region", "age", "category", "status"]


class PolicySearchQueryParams(BaseModel):
    q: str = Field(
        default="",
        description=(
            "자연어 검색어 (권장 최대 200자). q가 비어 있으면 region, age, "
            "category, status, keyword 중 하나 이상의 명시 조건이 필요함"
        ),
        max_length=200,
    )
    keyword: str | None = Field(
        default=None,
        description="명시적 키워드 필터 (q의 키워드 조건 override, 권장 최대 100자)",
        max_length=100,
    )
    region: str | None = Field(
        default=None,
        description="명시적 지역 alias/name 문자열 (q의 지역 조건 override, 권장 최대 100자)",
        max_length=100,
    )
    age: int | None = Field(
        default=None,
        ge=0,
        le=150,
        description="명시적 만 연령 (q의 연령 조건 override)",
    )
    category: PolicyCategory | None = Field(
        default=None,
        description="명시적 정책 카테고리 (q의 카테고리 override)",
    )
    status: ApplicationStatus | None = Field(
        default=None,
        description="신청 상태 필터 (open, scheduled, closed)",
    )
    include_partial: bool = Field(
        default=True,
        description="partial 데이터 포함 여부 (검색 API 기본값: true)",
    )
    page: int = Field(default=1, ge=1, description="페이지 번호")
    limit: int = Field(default=20, ge=1, le=100, description="페이지당 결과 수")
    sort: PolicySort = Field(
        default="default",
        description=(
            "정렬: default(관련도), title_asc, title_desc, deadline_asc, "
            "deadline_desc, collected_desc, collected_asc"
        ),
    )


class PolicySearchPreferences(BaseModel):
    region: str | None = Field(default=None, max_length=100)
    age: int | None = Field(default=None, ge=0, le=150)
    categories: list[PolicyCategory] = Field(
        default_factory=list,
        max_length=7,
    )


class PolicySearchPostRequest(PolicySearchQueryParams):
    preferences: PolicySearchPreferences | None = None


class ConditionItem(BaseModel):
    dimension: SearchDimension = Field(..., description="해석된 차원 종류")
    value: Any = Field(..., description="추출 또는 명시 지정된 차원 값")
    source: Literal["q", "explicit"] = Field(
        ..., description="조건 출처 (q: 자연어 파싱, explicit: 명시적 쿼리 파라미터)"
    )
    resolution: Literal["resolved", "unmapped", "ambiguous"] = Field(
        ..., description="해석 결과 상태"
    )
    candidates: list[str] = Field(
        default_factory=list, description="매핑 후보 문자열 리스트 (ambiguous/unmapped 시 대안 제공)"
    )


class InterpretedConditions(BaseModel):
    q_raw: str = Field(..., description="사용자가 입력한 원본 자연어 검색어")
    q_clean: str = Field(..., description="전처리 및 공백 정리된 검색어")
    conditions: list[ConditionItem] = Field(
        default_factory=list, description="차원별 상세 해석 조건 목록"
    )
    override_fields: list[SearchDimension] = Field(
        default_factory=list, description="명시적 필터 파라미터로 override된 차원 이름 목록"
    )
    uninterpreted_terms: list[str] = Field(
        default_factory=list, description="구조화 조건으로 해석되지 않은 독립 단어/토큰 목록"
    )


class DimensionVerdicts(BaseModel):
    region: Literal["match", "mismatch", "unknown"] | None = Field(
        default=None, description="지역 판정 (null: 차원 미적용, match: 부합, mismatch: 불일치, unknown: 데이터 부족)"
    )
    age: Literal["match", "mismatch", "unknown"] | None = Field(
        default=None, description="연령 판정 (null: 차원 미적용, match: 부합, mismatch: 불일치, unknown: 데이터 부족)"
    )
    status: Literal["match", "mismatch", "unknown"] | None = Field(
        default=None, description="신청상태 판정 (null: 차원 미적용, match: 부합, mismatch: 불일치, unknown: 데이터 부족)"
    )
    category: Literal["match", "mismatch", "unknown"] | None = Field(
        default=None, description="카테고리 판정 (null: 차원 미적용, match: 부합, mismatch: 불일치, unknown: 데이터 부족)"
    )


class UnconfirmedCondition(BaseModel):
    field: str = Field(..., description="미확인 차원/필드명 (예: 'region', 'age')")
    reason_code: str = Field(..., description="확장 가능한 머신 판독용 미확인 사유 코드")
    message: str = Field(..., description="사용자 표시용 설명 메시지")


class PolicySearchResultItem(BaseModel):
    policy: PolicyRead
    score: float = Field(
        ...,
        description="Backend 내부 ranking 점수 (높을수록 관련도 높음, 다른 요청 간 점수 비교 불가, Release 1 UI 미표시)",
    )
    verdicts: DimensionVerdicts = Field(
        ..., description="차원별 match/mismatch/unknown/null 판정"
    )
    unknown_count: int = Field(
        ..., description="verdicts 중 null을 제외하고 unknown인 차원의 개수"
    )
    reason_codes: list[str] = Field(
        default_factory=list, description="머신 판독용 판정 이유 코드 목록 (예: ['REGION_MATCH', 'AGE_UNKNOWN'])"
    )
    message: str = Field(..., description="사용자 표시용 조건 판정 요약 메시지")
    unconfirmed_conditions: list[UnconfirmedCondition] = Field(
        default_factory=list, description="원문 데이터 미비로 인한 unknown 설명 목록"
    )


class PolicySearchResponse(BaseModel):
    total: int = Field(..., description="pagination 적용 전 필터링 조건을 만족하는 총 결과 수")
    page: int = Field(..., description="현재 페이지 번호")
    limit: int = Field(..., description="페이지당 결과 수")
    interpreted_conditions: InterpretedConditions = Field(..., description="자연어 및 명시 필터 해석 메타데이터")
    items: list[PolicySearchResultItem] = Field(default_factory=list, description="검색 결과 정책 목록")
