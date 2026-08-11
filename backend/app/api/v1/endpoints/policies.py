from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.policy import PolicyRepository
from app.schemas.policy import PolicyListResponse, PolicyRead
from app.schemas.policy_search import PolicySearchResponse
from app.services.eligibility_evidence import build_eligibility_summary
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
    read_dto = PolicyRead.model_validate(policy)
    read_dto.eligibility_summary = build_eligibility_summary(policy)
    return read_dto
