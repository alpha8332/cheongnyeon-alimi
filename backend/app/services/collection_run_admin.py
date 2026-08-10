import math
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.collection_run import CollectionRun
from app.schemas.collection_run_admin import (
    CollectionRunAdminItem,
    CollectionRunAdminDetail,
    CollectionRunAdminListResponse,
)
from app.repositories.collection_run_admin import (
    get_admin_collection_runs,
    get_admin_collection_run_by_id,
)

# Stale 판단 기준: running 상태에서 시작 후 2시간(7,200초) 이상 지연 시
STALE_THRESHOLD_SECONDS = 7200


def check_is_stale(
    started_at: datetime,
    finished_at: Optional[datetime],
    status: str,
) -> bool:
    """
    CollectionRun의 Stale 상태 여부를 계산한다.
    status가 'running'이고 finished_at이 None이며 started_at으로부터 2시간 이상 지난 경우 True.
    """
    if status != "running" or finished_at is not None:
        return False

    now = datetime.now(timezone.utc)
    # timezone-naive datetime인 경우 UTC로 처리
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    elapsed_seconds = (now - started_at).total_seconds()
    return elapsed_seconds >= STALE_THRESHOLD_SECONDS


def list_admin_collection_runs_service(
    db: Session,
    page: int = 1,
    size: int = 20,
    source_id: Optional[str] = None,
    status: Optional[str] = None,
    run_type: Optional[str] = None,
    trigger_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> CollectionRunAdminListResponse:
    """CollectionRun 목록 조회 비즈니스 로직 및 DTO 변환."""
    items, total = get_admin_collection_runs(
        db=db,
        page=page,
        size=size,
        source_id=source_id,
        status=status,
        run_type=run_type,
        trigger_type=trigger_type,
        start_date=start_date,
        end_date=end_date,
    )

    pages = math.ceil(total / size) if total > 0 else 0

    dto_items = []
    for item in items:
        is_stale = check_is_stale(item.started_at, item.finished_at, str(item.status))
        dto_items.append(
            CollectionRunAdminItem(
                run_id=item.run_id,
                source_id=item.source_id,
                run_type=str(item.run_type),
                trigger_type=str(item.trigger_type),
                started_at=item.started_at,
                finished_at=item.finished_at,
                status=str(item.status),
                is_stale=is_stale,
                inserted_count=item.inserted_count,
                updated_count=item.updated_count,
                failed_count=item.failed_count,
                error_type=item.error_type,
            )
        )

    return CollectionRunAdminListResponse(
        items=dto_items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_admin_collection_run_detail_service(
    db: Session,
    run_id: UUID,
) -> Optional[CollectionRunAdminDetail]:
    """CollectionRun 단건 상세 조회 비즈니스 로직 및 DTO 변환."""
    item = get_admin_collection_run_by_id(db, run_id)
    if not item:
        return None

    is_stale = check_is_stale(item.started_at, item.finished_at, str(item.status))

    return CollectionRunAdminDetail(
        run_id=item.run_id,
        source_id=item.source_id,
        run_type=str(item.run_type),
        trigger_type=str(item.trigger_type),
        started_at=item.started_at,
        finished_at=item.finished_at,
        status=str(item.status),
        is_stale=is_stale,
        requested_count=item.requested_count,
        raw_document_count=item.raw_document_count,
        extracted_count=item.extracted_count,
        accepted_count=item.accepted_count,
        partial_count=item.partial_count,
        invalid_count=item.invalid_count,
        duplicate_count=item.duplicate_count,
        rejected_count=item.rejected_count,
        inserted_count=item.inserted_count,
        updated_count=item.updated_count,
        unchanged_count=item.unchanged_count,
        skipped_count=item.skipped_count,
        failed_count=item.failed_count,
        error_type=item.error_type,
    )
