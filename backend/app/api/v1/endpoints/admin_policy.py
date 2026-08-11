from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.endpoints.admin_access import get_current_admin_payload
from app.schemas.admin_policy import (
    AdminPolicyDetail,
    AdminPolicyListResponse,
    AdminPolicySortBy,
    SortOrder,
)
from app.services.admin_policy import (
    get_admin_policy_detail_service,
    list_admin_policies_service,
)

router = APIRouter()


@router.get(
    "",
    response_model=AdminPolicyListResponse,
    status_code=status.HTTP_200_OK,
    summary="관리자 정책 데이터 표 목록 조회 (Read-Only)",
    responses={
        200: {"description": "정책 데이터 목록 조회 성공"},
        401: {"description": "관리자 세션 인증 실패"},
        403: {"description": "권한 없음"},
    },
)
def get_admin_policies_endpoint(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=10, ge=1, le=100, description="페이지 당 항목 수 (최대 100)"),
    sort_by: AdminPolicySortBy = Query(default="id", description="Allowlist 정렬 컬럼"),
    order: SortOrder = Query(default="desc", description="정렬 순서 (asc, desc)"),
    category: Optional[str] = Query(default=None, description="카테고리 필터"),
    region: Optional[str] = Query(default=None, description="지역 필터"),
    source_id: Optional[str] = Query(default=None, description="수집 출처 ID 필터"),
    status_param: Optional[str] = Query(default=None, alias="status", description="신청 상태 필터"),
    data_quality_status: Optional[str] = Query(default=None, description="데이터 품질 상태 필터 (valid, partial)"),
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(get_current_admin_payload),
) -> AdminPolicyListResponse:
    """
    인증된 관리자 전용 읽기 전용 정책 데이터 표 목록을 반환한다.
    - SQL injection 방지: Allowlist 기반 정렬만 허용.
    - 최대 limit 100 강제.
    """
    return list_admin_policies_service(
        db=db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        order=order,
        category=category,
        region=region,
        source_id=source_id,
        status=status_param,
        data_quality_status=data_quality_status,
    )


@router.get(
    "/{policy_id}",
    response_model=AdminPolicyDetail,
    status_code=status.HTTP_200_OK,
    summary="관리자 정책 데이터 단건 상세 조회 (Read-Only)",
    responses={
        200: {"description": "정책 데이터 상세 조회 성공"},
        401: {"description": "관리자 세션 인증 실패"},
        403: {"description": "권한 없음"},
        404: {"description": "해당 정책을 찾을 수 없음"},
    },
)
def get_admin_policy_detail_endpoint(
    policy_id: int,
    db: Session = Depends(get_db),
    admin_payload: dict = Depends(get_current_admin_payload),
) -> AdminPolicyDetail:
    """인증된 관리자 전용 읽기 전용 정책 데이터 단건 상세 정보를 반환한다."""
    detail = get_admin_policy_detail_service(db=db, policy_id=policy_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin policy not found",
        )
    return detail
