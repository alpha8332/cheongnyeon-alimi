from typing import Optional
from sqlalchemy.orm import Session

from app.repositories.admin_policy import get_admin_policies, get_admin_policy_by_id
from app.schemas.admin_policy import (
    AdminPolicyDetail,
    AdminPolicyItem,
    AdminPolicyListResponse,
)


def list_admin_policies_service(
    db: Session,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    order: str = "desc",
    category: Optional[str] = None,
    region: Optional[str] = None,
    source_id: Optional[str] = None,
    status: Optional[str] = None,
    data_quality_status: Optional[str] = None,
) -> AdminPolicyListResponse:
    """관리자 전용 읽기 정책 데이터 목록 조회 서비스."""
    # 최대 limit 100 강제
    safe_limit = min(max(limit, 1), 100)
    safe_page = max(page, 1)

    items, total = get_admin_policies(
        db=db,
        page=safe_page,
        limit=safe_limit,
        sort_by=sort_by,
        order=order,
        category=category,
        region=region,
        source_id=source_id,
        status=status,
        data_quality_status=data_quality_status,
    )

    item_dtos = [AdminPolicyItem.model_validate(p) for p in items]

    return AdminPolicyListResponse(
        total=total,
        page=safe_page,
        limit=safe_limit,
        items=item_dtos,
    )


def get_admin_policy_detail_service(
    db: Session,
    policy_id: int,
) -> Optional[AdminPolicyDetail]:
    """관리자 전용 읽기 정책 데이터 단건 상세 조회 서비스."""
    policy = get_admin_policy_by_id(db, policy_id)
    if policy is None:
        return None
    return AdminPolicyDetail.model_validate(policy)
