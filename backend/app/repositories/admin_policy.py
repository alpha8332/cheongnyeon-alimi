from typing import List, Optional, Tuple
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.models.policy import Policy

ALLOWLIST_SORT_FIELDS = {
    "id": Policy.id,
    "created_at": Policy.created_at,
    "updated_at": Policy.updated_at,
    "title": Policy.title,
    "collected_at": Policy.collected_at,
}


def get_admin_policies(
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
) -> Tuple[List[Policy], int]:
    """
    관리자 읽기 전용 정책 데이터 표 목록 조회.
    - SQL injection 방지를 위해 ALLOWLIST_SORT_FIELDS에 지정된 필드만 정렬 허용.
    - 최대 limit 100 강제.
    """
    query = db.query(Policy)

    # 필터 적용
    if source_id:
        query = query.filter(Policy.source_id == source_id)
    if status:
        query = query.filter(Policy.application_status == status)
    if data_quality_status:
        query = query.filter(Policy.data_quality_status == data_quality_status)

    total = query.count()

    # Allowlist 기반 정렬 적용
    sort_column = ALLOWLIST_SORT_FIELDS.get(sort_by, Policy.id)
    if order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # 페이징 적용
    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()

    # 인메모리 category / region 추가 필터링 (JSONB 내 필터)
    if category or region:
        filtered_items = []
        for policy in items:
            cat_match = not category or (policy.categories and category in policy.categories)
            reg_match = not region or (not policy.regions or "전국" in policy.regions or region in policy.regions)
            if cat_match and reg_match:
                filtered_items.append(policy)
        items = filtered_items

    return items, total


def get_admin_policy_by_id(db: Session, policy_id: int) -> Optional[Policy]:
    """관리자 읽기 전용 정책 데이터 단건 상세 조회."""
    return db.query(Policy).filter(Policy.id == policy_id).first()
