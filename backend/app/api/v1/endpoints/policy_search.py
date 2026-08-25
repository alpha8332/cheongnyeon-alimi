from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.policy_search import PolicySearchRepository
from app.schemas.policy import PolicySort
from app.schemas.policy_search import (
    PolicySearchPostRequest,
    PolicySearchPreferences,
    PolicySearchQueryParams,
    PolicySearchResponse,
)
from app.services.policy_search_parser import parse_search_query

router = APIRouter()

CategoryQuery = Literal[
    "housing",
    "finance",
    "welfare",
    "employment",
    "startup",
    "education",
    "other",
]
ApplicationStatusQuery = Literal["open", "closed", "scheduled"]


def _execute_policy_search(
    request: PolicySearchQueryParams,
    db: Session,
    *,
    preferences: PolicySearchPreferences | None = None,
) -> PolicySearchResponse:
    # 1. q 파라미터 공백 검증 (q_raw 원문 보존 전달)
    q_raw = request.q
    q_clean = request.q.strip()
    if not q_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=[
                {
                    "loc": ["query", "q"],
                    "msg": "q parameter must not be empty or blank",
                    "type": "value_error",
                }
            ],
        )

    # 2. q_raw 원문을 파서에 넘김 (q_raw 보존 계약)
    interpreted = parse_search_query(
        q=q_raw,
        keyword=request.keyword,
        region=request.region,
        age=request.age,
        category=request.category,
        status=request.status,
        db=db,
    )

    # 3. 해석 예외 검증
    # 명시적 region 해석 실패 (unmapped / ambiguous) -> 400 Bad Request
    cond_map = {cond.dimension: cond for cond in interpreted.conditions}
    explicit_region_cond = cond_map.get("region")
    if explicit_region_cond and explicit_region_cond.source == "explicit":
        if explicit_region_cond.resolution in ("unmapped", "ambiguous"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "message": f"올바르지 않은 명시적 지역 조건입니다: {explicit_region_cond.value}",
                        "details": {
                            "field": "region",
                            "value": explicit_region_cond.value,
                            "resolution": explicit_region_cond.resolution,
                            "candidates": explicit_region_cond.candidates,
                        },
                    }
                },
            )

    # 사용할 수 있는 검색 조건/토큰이 전혀 없음 -> 400 Bad Request
    if not interpreted.conditions and not interpreted.uninterpreted_terms:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "message": "유효한 검색어 또는 구조화 조건이 제공되지 않았습니다.",
                    "details": {},
                }
            },
        )

    # 4. Repository search 조회
    repo = PolicySearchRepository(db)
    items, total = repo.search_policies(
        interpreted,
        preferences=preferences,
        include_partial=request.include_partial,
        page=request.page,
        limit=request.limit,
        sort=request.sort,
    )

    return PolicySearchResponse(
        total=total,
        page=request.page,
        limit=request.limit,
        interpreted_conditions=interpreted,
        items=items,
    )


@router.get("/search", response_model=PolicySearchResponse, summary="정책 자연어 검색")
def search_policies_api(
    q: str = Query(
        ...,
        description="자연어 검색어 (공백 제거 후 1자 이상 필수, 권장 최대 200자)",
        max_length=200,
    ),
    keyword: Annotated[
        str | None,
        Query(max_length=100, description="명시적 키워드 필터"),
    ] = None,
    region: Annotated[
        str | None,
        Query(max_length=100, description="명시적 지역 alias/name 문자열"),
    ] = None,
    age: Annotated[
        int | None,
        Query(ge=0, le=150, description="명시적 만 연령"),
    ] = None,
    category: Annotated[
        CategoryQuery | None,
        Query(description="명시적 정책 카테고리"),
    ] = None,
    status_param: Annotated[
        ApplicationStatusQuery | None,
        Query(alias="status", description="신청 상태 필터"),
    ] = None,
    include_partial: bool = Query(
        True,
        description="partial 정책 포함 여부 (기본값: true)",
    ),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지 당 결과 수"),
    sort: PolicySort = Query(
        "default",
        description=(
            "정렬: default(관련도), title_asc, title_desc, deadline_asc, "
            "deadline_desc, collected_desc, collected_asc"
        ),
    ),
    db: Session = Depends(get_db),
) -> PolicySearchResponse:
    request = PolicySearchQueryParams(
        q=q,
        keyword=keyword,
        region=region,
        age=age,
        category=category,
        status=status_param,
        include_partial=include_partial,
        page=page,
        limit=limit,
        sort=sort,
    )
    return _execute_policy_search(request, db)


@router.post(
    "/search",
    response_model=PolicySearchResponse,
    summary="프로필 우선순위 정책 자연어 검색",
)
def search_policies_with_preferences_api(
    request: PolicySearchPostRequest,
    db: Session = Depends(get_db),
) -> PolicySearchResponse:
    return _execute_policy_search(
        request,
        db,
        preferences=request.preferences,
    )
