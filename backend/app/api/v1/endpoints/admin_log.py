from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.endpoints.admin_access import get_current_admin_payload
from app.schemas.admin_log import (
    LogDeleteResponse,
    LogEventListResponse,
    LogFileListResponse,
)
from app.services.admin_log import (
    delete_archived_log_file_service,
    get_log_events_service,
    list_log_files_service,
)

router = APIRouter()


@router.get(
    "/files",
    response_model=LogFileListResponse,
    status_code=status.HTTP_200_OK,
    summary="로그 파일 목록 조회",
    responses={
        200: {"description": "로그 파일 목록 조회 성공"},
        401: {"description": "관리자 세션 인증 실패"},
        403: {"description": "권한 없음"},
    },
)
def get_log_files_endpoint(
    admin_payload: dict = Depends(get_current_admin_payload),
) -> LogFileListResponse:
    """인증된 관리자 전용 서버 로그 파일 목록을 반환한다."""
    return list_log_files_service()


@router.get(
    "/events",
    response_model=LogEventListResponse,
    status_code=status.HTTP_200_OK,
    summary="파싱된 로그 이벤트 목록 조회",
    responses={
        200: {"description": "로그 이벤트 목록 조회 성공"},
        400: {"description": "유효하지 않거나 안전하지 않은 file_id"},
        401: {"description": "관리자 세션 인증 실패"},
        403: {"description": "권한 없음"},
    },
)
def get_log_events_endpoint(
    file_id: str = Query(default="app.log", description="조회 대상 로그 파일 ID"),
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지 당 항목 수"),
    level: Optional[str] = Query(default=None, description="로그 레벨 필터 (INFO, ERROR 등)"),
    component: Optional[str] = Query(default=None, description="컴포넌트 필터"),
    query_str: Optional[str] = Query(default=None, alias="q", description="이벤트 검색어"),
    admin_payload: dict = Depends(get_current_admin_payload),
) -> LogEventListResponse:
    """인증된 관리자 전용 파싱된 JSON Lines 로그 이벤트 목록을 페이징 및 필터하여 반환한다."""
    try:
        return get_log_events_service(
            file_id=file_id,
            page=page,
            limit=limit,
            level=level,
            component=component,
            query_str=query_str,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/archives/{file_id}",
    response_model=LogDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="회전된 Archive 로그 파일 삭제 (감사 기록 생성)",
    responses={
        200: {"description": "로그 archive 파일 삭제 성공"},
        400: {"description": "활성 파일(app.log) 직접 삭제 시도 또는 안전하지 않은 경로"},
        401: {"description": "관리자 세션 인증 실패"},
        403: {"description": "권한 없음"},
        404: {"description": "대상 archive 로그 파일을 찾을 수 없음"},
    },
)
def delete_log_archive_endpoint(
    file_id: str,
    admin_payload: dict = Depends(get_current_admin_payload),
) -> LogDeleteResponse:
    """
    회전 완료된 Archive 로그 파일만 안전하게 삭제하고 별도 감사 기록(Audit Trail)을 생성한다.
    - 활성 파일(app.log) 직접 삭제 차단 (400 Bad Request)
    - Path Traversal 차단 (400 Bad Request)
    """
    try:
        admin_id = admin_payload.get("sub", "admin")
        return delete_archived_log_file_service(file_id=file_id, admin_id=admin_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
