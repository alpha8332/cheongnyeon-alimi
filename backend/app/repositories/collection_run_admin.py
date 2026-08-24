from datetime import datetime, timezone
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.collection_run import CollectionRun


def get_admin_collection_runs(
    db: Session,
    page: int = 1,
    size: int = 20,
    source_id: Optional[str] = None,
    status: Optional[str] = None,
    run_type: Optional[str] = None,
    trigger_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Tuple[List[CollectionRun], int]:
    """
    관리자용 CollectionRun 목록 및 총 개수 조회 (필터 및 페이징 적용).
    기본 정렬: started_at DESC
    """
    query = db.query(CollectionRun)

    if source_id:
        query = query.filter(CollectionRun.source_id == source_id)
    if status:
        query = query.filter(CollectionRun.status == status)
    if run_type:
        query = query.filter(CollectionRun.run_type == run_type)
    if trigger_type:
        query = query.filter(CollectionRun.trigger_type == trigger_type)
    if start_date:
        query = query.filter(CollectionRun.started_at >= start_date)
    if end_date:
        query = query.filter(CollectionRun.started_at <= end_date)

    total = query.count()

    offset = (page - 1) * size
    items = query.order_by(desc(CollectionRun.started_at)).offset(offset).limit(size).all()

    return items, total


def get_admin_collection_run_by_id(
    db: Session,
    run_id: UUID,
) -> Optional[CollectionRun]:
    """run_id 기준 CollectionRun 단건 상세 조회."""
    return db.query(CollectionRun).filter(CollectionRun.run_id == run_id).first()


def get_active_running_collection_run(
    db: Session,
    source_id: Optional[str] = None,
) -> Optional[CollectionRun]:
    """
    특정 source_id(또는 전체)에 대해 queued/running 활성 수집건 조회.
    최신 started_at 항목을 먼저 반환한다.
    """
    query = db.query(CollectionRun).filter(
        CollectionRun.status.in_(("queued", "running")),
        CollectionRun.finished_at.is_(None),
    )
    if source_id:
        query = query.filter(CollectionRun.source_id == source_id)

    return query.order_by(desc(CollectionRun.started_at)).first()


def create_admin_collection_run(
    db: Session,
    source_id: Optional[str] = "youthcenter",
    requested_count: int = 100,
    run_type: str = "collection",
    trigger_type: str = "admin",
) -> CollectionRun:
    """브로커 발행 전에 새 수동 수집 실행 기록을 queued로 저장한다."""
    new_run = CollectionRun(
        source_id=source_id,
        run_type=run_type,
        trigger_type=trigger_type,
        status="queued",
        requested_count=requested_count,
        started_at=datetime.now(timezone.utc),
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)
    return new_run
