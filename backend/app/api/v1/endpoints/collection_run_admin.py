from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_admin_payload
from app.schemas.collection_run_admin import (
    CollectionRunAdminListResponse,
    CollectionRunAdminDetail,
)
from app.services.collection_run_admin import (
    list_admin_collection_runs_service,
    get_admin_collection_run_detail_service,
)

router = APIRouter()


@router.get(
    "",
    response_model=CollectionRunAdminListResponse,
    status_code=status.HTTP_200_OK,
    summary="CollectionRun 관리자 실행 이력 목록 조회",
    responses={
        200: {"description": "CollectionRun 목록 조회 성공"},
        401: {"description": "관리자 토큰 미제공 또는 유효하지 않음"},
        403: {"description": "관리자 권한 부족"},
        422: {"description": "파라미터 유효성 검사 실패"},
    },
)
def list_collection_runs(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    size: int = Query(default=20, ge=1, le=100, description="페이지 당 항목 수"),
    source_id: Optional[str] = Query(default=None, description="수집원 ID 필터"),
    status_param: Optional[str] = Query(default=None, alias="status", description="수집 상태 필터 (running, succeeded, partial_failure, failed)"),
    run_type: Optional[str] = Query(default=None, description="실행 유형 필터 (seed_import, runtime_import, collection)"),
    trigger_type: Optional[str] = Query(default=None, description="트리거 주체 필터 (cli, scheduler, admin)"),
    start_date: Optional[datetime] = Query(default=None, description="검색 시작 일시"),
    end_date: Optional[datetime] = Query(default=None, description="검색 종료 일시"),
    db: Session = Depends(get_db),
    admin_payload: Dict[str, Any] = Depends(get_current_admin_payload),
) -> CollectionRunAdminListResponse:
    """
    관리자 전용 CollectionRun 실행 이력 목록을 페이징 및 필터링하여 조회한다.
    기본 정렬: started_at DESC
    """
    return list_admin_collection_runs_service(
        db=db,
        page=page,
        size=size,
        source_id=source_id,
        status=status_param,
        run_type=run_type,
        trigger_type=trigger_type,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/{run_id}",
    response_model=CollectionRunAdminDetail,
    status_code=status.HTTP_200_OK,
    summary="CollectionRun 관리자 단건 상세 조회",
    responses={
        200: {"description": "CollectionRun 상세 조회 성공"},
        401: {"description": "관리자 토큰 미제공 또는 유효하지 않음"},
        403: {"description": "관리자 권한 부족"},
        404: {"description": "존재하지 않는 run_id"},
        422: {"description": "UUID 규격 미충족"},
    },
)
def get_collection_run_detail(
    run_id: UUID,
    db: Session = Depends(get_db),
    admin_payload: Dict[str, Any] = Depends(get_current_admin_payload),
) -> CollectionRunAdminDetail:
    """
    run_id 기준 CollectionRun 단건 상세 정보를 조회한다.
    존재하지 않는 run_id인 경우 404 Not Found를 반환한다.
    """
    detail = get_admin_collection_run_detail_service(db, run_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection run '{run_id}' not found.",
        )
    return detail
