from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.policy import PolicyRepository
from app.schemas.policy import PolicyListResponse, PolicyRead
from app.schemas.policy_search import PolicySearchResponse
from app.services.policy import PolicyListRequest, PolicyService

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


def get_policy_service(
    db: Session = Depends(get_db),
) -> PolicyService:
    return PolicyService(PolicyRepository(db))


@router.get("", response_model=PolicyListResponse, summary="정책 목록 조회")
def get_policies(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
    category: Annotated[
        CategoryQuery | None,
        Query(description="정규화 카테고리의 정확한 배열 원소"),
    ] = None,
    region: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description="정규화 지역의 정확한 배열 원소",
        ),
    ] = None,
    application_status: Annotated[
        ApplicationStatusQuery | None,
        Query(alias="status", description="신청 상태"),
    ] = None,
    include_partial: bool = Query(
        False,
        description="partial 정책 포함 여부; 기본값은 valid만",
    ),
    service: PolicyService = Depends(get_policy_service),
) -> PolicyListResponse:
    selected = service.list(
        PolicyListRequest(
            page=page,
            limit=limit,
            category=category,
            region=region,
            application_status=application_status,
            include_partial=include_partial,
        )
    )

    return PolicyListResponse(
        total=selected.total,
        page=page,
        limit=limit,
        items=list(selected.items),
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
    db: Session = Depends(get_db),
) -> PolicySearchResponse:
    from fastapi.responses import JSONResponse
    from app.repositories.policy_search import PolicySearchRepository
    from app.schemas.policy_search import PolicySearchResponse
    from app.services.policy_search_parser import parse_search_query

    q_clean = q.strip()
    if not q_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["query", "q"],
                    "msg": "q parameter must not be empty or blank",
                    "type": "value_error",
                }
            ],
        )

    interpreted = parse_search_query(
        q=q_clean,
        keyword=keyword,
        region=region,
        age=age,
        category=category,
        status=status_param,
        db=db,
    )

    # 해석 예외 검증
    # 1. 명시적 region 해석 실패 (unmapped / ambiguous) -> 400 Bad Request
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

    # 2. 사용할 수 있는 검색 조건/토큰이 전혀 없음 -> 400 Bad Request
    if not interpreted.conditions and not interpreted.uninterpreted_terms and not interpreted.q_clean:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "message": "유효한 검색어 또는 구조화 조건이 제공되지 않았습니다.",
                    "details": {},
                }
            },
        )

    # Repository search 조회
    repo = PolicySearchRepository(db)
    items, total = repo.search_policies(
        interpreted,
        include_partial=include_partial,
        page=page,
        limit=limit,
    )

    return PolicySearchResponse(
        total=total,
        page=page,
        limit=limit,
        interpreted_conditions=interpreted,
        items=items,
    )


@router.get("/{policy_id}", response_model=PolicyRead, summary="정책 상세 조회")
def get_policy_detail(
    policy_id: int,
    include_partial: bool = Query(
        False,
        description="partial 정책 상세 조회 허용 여부; 기본값은 valid만",
    ),
    service: PolicyService = Depends(get_policy_service),
) -> PolicyRead:
    policy = service.get(
        policy_id,
        include_partial=include_partial,
    )
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )
    return policy
