from typing import List, Optional, Tuple
from sqlalchemy import asc, desc, exists, func, or_, select
from sqlalchemy.orm import Session

from app.models.policy import Policy

ALLOWLIST_SORT_FIELDS = {
    "id": Policy.id,
    "created_at": Policy.created_at,
    "updated_at": Policy.updated_at,
    "title": Policy.title,
    "collected_at": Policy.collected_at,
}


def _json_array_contains(db: Session, column, value: str):
    """Build a database-side JSON array membership predicate."""

    if db.get_bind().dialect.name == "sqlite":
        values = func.json_each(column).table_valued("key", "value").alias()
        return exists(select(1).select_from(values).where(values.c.value == value))
    return column.contains([value])


def _json_array_is_empty(db: Session, column):
    if db.get_bind().dialect.name == "postgresql":
        return func.jsonb_array_length(column) == 0
    return func.json_array_length(column) == 0


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
    if category:
        query = query.filter(_json_array_contains(db, Policy.categories, category))
    if region:
        query = query.filter(
            or_(
                _json_array_is_empty(db, Policy.regions),
                _json_array_contains(db, Policy.regions, "전국"),
                _json_array_contains(db, Policy.regions, region),
            )
        )

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

    return items, total


def get_admin_policy_by_id(db: Session, policy_id: int) -> Optional[Policy]:
    """관리자 읽기 전용 정책 데이터 단건 상세 조회."""
    return db.query(Policy).filter(Policy.id == policy_id).first()
